import asyncio
import ipaddress
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal
from urllib.parse import quote
from uuid import uuid4

import httpx
from fastapi import Request

from app.config import Settings

Action = Literal["access_verify", "scan_analyze"]
Provider = Literal["gemini", "prototype", "api_provider", "local_vlm"]
ProviderOutcome = Literal["succeeded", "failed", "not_called"]
ErrorCategory = Literal[
    "auth_failed",
    "validation_failed",
    "provider_timeout",
    "provider_rejected",
    "provider_invalid_response",
    "persistence_failed",
    "internal_error",
]
IpSource = Literal[
    "x-vercel-forwarded-for",
    "x-forwarded-for",
    "unavailable",
    "invalid",
]

AUDITED_ROUTES: dict[tuple[str, str], Action] = {
    ("GET", "/access/verify"): "access_verify",
    ("POST", "/api/scans/analyze"): "scan_analyze",
}

logger = logging.getLogger("farmscout.audit")


class AuditWriteError(RuntimeError):
    pass


@dataclass(frozen=True)
class AuditEvent:
    schema_version: str
    event_id: str
    occurred_at_utc: str
    request_id: str
    environment: Literal["production", "preview", "development"]
    action: Action
    client_ip: str | None
    ip_source: IpSource
    external_api_used: bool
    provider: Provider | None
    provider_outcome: ProviderOutcome
    outcome: Literal["succeeded", "failed"]
    http_status: int
    error_category: ErrorCategory | None

    def to_payload(self) -> dict[str, object]:
        # Deliberately construct the complete allowlist field by field. Never
        # merge request, response, exception, provider, or framework objects.
        return {
            "schema_version": self.schema_version,
            "event_id": self.event_id,
            "occurred_at_utc": self.occurred_at_utc,
            "request_id": self.request_id,
            "environment": self.environment,
            "action": self.action,
            "client_ip": self.client_ip,
            "ip_source": self.ip_source,
            "external_api_used": self.external_api_used,
            "provider": self.provider,
            "provider_outcome": self.provider_outcome,
            "outcome": self.outcome,
            "http_status": self.http_status,
            "error_category": self.error_category,
        }


def trusted_client_ip(request: Request, settings: Settings) -> tuple[str | None, IpSource]:
    if settings.vercel != "1":
        return None, "unavailable"

    source: IpSource
    raw_value = request.headers.get("x-vercel-forwarded-for")
    if raw_value is not None:
        source = "x-vercel-forwarded-for"
    else:
        raw_value = request.headers.get("x-forwarded-for")
        source = "x-forwarded-for" if raw_value is not None else "unavailable"

    if raw_value is None:
        return None, "unavailable"
    candidate = raw_value.strip()
    if not candidate or "," in candidate:
        return None, "invalid"
    try:
        return str(ipaddress.ip_address(candidate)), source
    except ValueError:
        return None, "invalid"


def audit_environment(settings: Settings) -> Literal["production", "preview", "development"]:
    if settings.vercel == "1" and settings.vercel_env in {"production", "preview", "development"}:
        return settings.vercel_env
    return "development"


def configure_provider_audit(request: Request, provider: str, settings: Settings) -> None:
    external_provider: Provider | None = None
    if provider == "gemini":
        external_provider = "gemini"
    elif provider == "prototype":
        external_provider = "prototype"
    elif provider == "local_vlm":
        external_provider = "local_vlm"
    elif provider == "api_provider" and (settings.openai_api_key or settings.anthropic_api_key):
        external_provider = "api_provider"

    request.state.audit_external_api_used = external_provider is not None
    request.state.audit_provider = external_provider
    request.state.audit_provider_outcome = "failed" if external_provider else "not_called"


def provider_error_category(exc: Exception) -> ErrorCategory:
    if isinstance(exc, httpx.TimeoutException):
        return "provider_timeout"
    if isinstance(exc, httpx.HTTPStatusError):
        return "provider_rejected"
    message = str(exc).lower()
    if "timeout" in message or "timed out" in message:
        return "provider_timeout"
    if "rejected" in message or "status code" in message:
        return "provider_rejected"
    if "invalid structured" in message or "invalid response" in message or "returned no analysis" in message:
        return "provider_invalid_response"
    return "internal_error"


def build_audit_event(
    request: Request,
    settings: Settings,
    action: Action,
    http_status: int,
    request_id: str,
) -> AuditEvent:
    client_ip, ip_source = trusted_client_ip(request, settings)
    error_category = getattr(request.state, "audit_error_category", None)
    if http_status < 400:
        error_category = None
    elif error_category is None:
        if http_status == 401:
            error_category = "auth_failed"
        elif http_status == 422:
            error_category = "validation_failed"
        elif http_status == 503 and action == "scan_analyze":
            error_category = "persistence_failed"
        else:
            error_category = "internal_error"

    return AuditEvent(
        schema_version="1",
        event_id=str(uuid4()),
        occurred_at_utc=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        request_id=request_id,
        environment=audit_environment(settings),
        action=action,
        client_ip=client_ip,
        ip_source=ip_source,
        external_api_used=bool(getattr(request.state, "audit_external_api_used", False)),
        provider=getattr(request.state, "audit_provider", None),
        provider_outcome=getattr(request.state, "audit_provider_outcome", "not_called"),
        outcome="succeeded" if http_status < 400 else "failed",
        http_status=http_status,
        error_category=error_category,
    )


class CloudAuditWriter:
    def __init__(self, settings: Settings, client: httpx.AsyncClient | None = None):
        self.settings = settings
        self._client = client
        self._access_token: str | None = None
        self._access_token_expires_at = 0.0
        self._token_lock = asyncio.Lock()

    def _configuration(self) -> tuple[str, str, str, str, str, str]:
        values = (
            self.settings.gcp_project_id,
            self.settings.gcp_project_number,
            self.settings.gcp_service_account_email,
            self.settings.gcp_workload_identity_pool_id,
            self.settings.gcp_workload_identity_pool_provider_id,
            self.settings.gcp_audit_log_id,
        )
        if not all(values):
            raise AuditWriteError("Audit logging is not configured")
        return values  # type: ignore[return-value]

    async def _request(self, method: str, url: str, **kwargs: object) -> httpx.Response:
        try:
            if self._client:
                return await self._client.request(method, url, **kwargs)
            async with httpx.AsyncClient(timeout=15) as client:
                return await client.request(method, url, **kwargs)
        except httpx.HTTPError as exc:
            raise AuditWriteError("Audit transport failed") from exc

    async def write(self, event: AuditEvent, oidc_token: str | None) -> None:
        project_id, _, _, _, _, log_id = self._configuration()
        access_token = await self._get_access_token(oidc_token)
        response = await self._request(
            "POST",
            "https://logging.googleapis.com/v2/entries:write",
            headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
            json={
                "logName": f"projects/{project_id}/logs/{log_id}",
                "resource": {"type": "global", "labels": {"project_id": project_id}},
                "entries": [{"jsonPayload": event.to_payload()}],
                "partialSuccess": False,
            },
        )
        if response.is_error:
            raise AuditWriteError("Cloud Logging write failed")

    async def _get_access_token(self, oidc_token: str | None) -> str:
        if self._access_token and time.monotonic() < self._access_token_expires_at - 60:
            return self._access_token
        if not oidc_token:
            raise AuditWriteError("Vercel OIDC token is unavailable")

        async with self._token_lock:
            if self._access_token and time.monotonic() < self._access_token_expires_at - 60:
                return self._access_token
            _, project_number, service_account, pool_id, provider_id, _ = self._configuration()
            audience = (
                f"//iam.googleapis.com/projects/{project_number}/locations/global/"
                f"workloadIdentityPools/{pool_id}/providers/{provider_id}"
            )
            sts_response = await self._request(
                "POST",
                "https://sts.googleapis.com/v1/token",
                headers={"Content-Type": "application/json"},
                json={
                    "audience": audience,
                    "grantType": "urn:ietf:params:oauth:grant-type:token-exchange",
                    "requestedTokenType": "urn:ietf:params:oauth:token-type:access_token",
                    "scope": "https://www.googleapis.com/auth/cloud-platform",
                    "subjectToken": oidc_token,
                    "subjectTokenType": "urn:ietf:params:oauth:token-type:id_token",
                },
            )
            if sts_response.is_error:
                raise AuditWriteError("OIDC token exchange failed")
            try:
                federated_token = sts_response.json()["access_token"]
            except (KeyError, TypeError, ValueError) as exc:
                raise AuditWriteError("OIDC token exchange returned invalid data") from exc

            encoded_account = quote(service_account, safe="")
            iam_response = await self._request(
                "POST",
                (
                    "https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/"
                    f"{encoded_account}:generateAccessToken"
                ),
                headers={"Authorization": f"Bearer {federated_token}", "Content-Type": "application/json"},
                json={
                    "scope": ["https://www.googleapis.com/auth/logging.write"],
                    "lifetime": "900s",
                },
            )
            if iam_response.is_error:
                raise AuditWriteError("Service account impersonation failed")
            try:
                self._access_token = iam_response.json()["accessToken"]
            except (KeyError, TypeError, ValueError) as exc:
                raise AuditWriteError("Service account impersonation returned invalid data") from exc
            self._access_token_expires_at = time.monotonic() + 900
            return self._access_token


async def emit_audit_safely(
    writer: CloudAuditWriter,
    event: AuditEvent,
    oidc_token: str | None,
) -> None:
    try:
        await writer.write(event, oidc_token)
    except Exception:
        # Fixed operational signal only. Never include the event, IP, token,
        # request/response content, or exception details, and never recurse.
        logger.error("FarmScout audit write failed")

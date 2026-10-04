import json
import unittest
from datetime import datetime, timezone
from unittest.mock import patch
from uuid import uuid4

import httpx
from fastapi.testclient import TestClient
from starlette.requests import Request

from app.audit import AuditEvent, CloudAuditWriter, build_audit_event, trusted_client_ip
from app.config import Settings
from app.main import app, settings
from app.schemas import AnalyzeScanResponse, PersistedAnalyzeScanResponse


class CapturingWriter:
    def __init__(self, fail: bool = False):
        self.events: list[AuditEvent] = []
        self.tokens: list[str | None] = []
        self.fail = fail

    async def write(self, event: AuditEvent, oidc_token: str | None) -> None:
        self.events.append(event)
        self.tokens.append(oidc_token)
        if self.fail:
            raise RuntimeError("synthetic audit failure")


def request_with_headers(headers: dict[str, str]) -> Request:
    return Request({
        "type": "http",
        "method": "GET",
        "path": "/access/verify",
        "headers": [(key.lower().encode(), value.encode()) for key, value in headers.items()],
    })


def complete_analysis() -> AnalyzeScanResponse:
    return AnalyzeScanResponse(
        crop_is_lettuce=True,
        crop_confidence=0.96,
        image_quality={"usable": True, "issues": [], "retake_guidance": []},
        plant_stress_detected=False,
        stress_level="none",
        severity_score=0,
        confidence=0.92,
        diagnosis="Healthy",
        observed_symptoms=[],
        possible_causes=[],
        detected_issues=[],
        recommendations=[],
        needs_human_review=False,
    )


class FakeProvider:
    def __init__(self, error: Exception | None = None):
        self.error = error

    async def analyze(self, _request):
        if self.error:
            raise self.error
        return complete_analysis()


class FakeStore:
    def __init__(self, _settings):
        pass

    async def persist_success(self, _request, analysis, _model_name):
        return PersistedAnalyzeScanResponse(
            **analysis.model_dump(mode="json"),
            scan_id=uuid4(),
            created_at=datetime.now(timezone.utc),
        )


class FailingStore:
    def __init__(self, _settings):
        pass

    async def persist_success(self, _request, _analysis, _model_name):
        from app.supabase_persistence import PersistenceError

        raise PersistenceError("synthetic persistence failure")


class AuditUnitTests(unittest.IsolatedAsyncioTestCase):
    def audit_settings(self) -> Settings:
        return Settings(
            _env_file=None,
            gcp_project_id="vlm-api-2026-001",
            gcp_project_number="694852084507",
            gcp_service_account_email="farmscout-audit-writer@vlm-api-2026-001.iam.gserviceaccount.com",
            gcp_workload_identity_pool_id="farmscout-vercel",
            gcp_workload_identity_pool_provider_id="farm-scout-production",
            gcp_audit_log_id="farmscout-access-audit",
            vercel="1",
            vercel_env="production",
        )

    def test_trusted_ip_prefers_vercel_header_and_rejects_lists(self) -> None:
        configured = self.audit_settings()
        address, source = trusted_client_ip(
            request_with_headers({
                "x-vercel-forwarded-for": "2001:0db8::1",
                "x-forwarded-for": "198.51.100.10",
            }),
            configured,
        )
        self.assertEqual(address, "2001:db8::1")
        self.assertEqual(source, "x-vercel-forwarded-for")

        address, source = trusted_client_ip(
            request_with_headers({"x-vercel-forwarded-for": "198.51.100.1, 198.51.100.2"}),
            configured,
        )
        self.assertIsNone(address)
        self.assertEqual(source, "invalid")

        configured.vercel = None
        address, source = trusted_client_ip(
            request_with_headers({"x-vercel-forwarded-for": "198.51.100.1"}),
            configured,
        )
        self.assertIsNone(address)
        self.assertEqual(source, "unavailable")

    def test_payload_is_exact_allowlist_without_forbidden_content(self) -> None:
        incoming = request_with_headers({"x-vercel-forwarded-for": "198.51.100.7"})
        event = build_audit_event(incoming, self.audit_settings(), "access_verify", 200, str(uuid4()))
        payload = event.to_payload()
        self.assertEqual(set(payload), {
            "schema_version", "event_id", "occurred_at_utc", "request_id", "environment",
            "action", "client_ip", "ip_source", "external_api_used", "provider",
            "provider_outcome", "outcome", "http_status", "error_category",
        })
        serialized = json.dumps(payload)
        for forbidden in (
            "authorization", "cookie", "access_code", "image", "base64", "scan_id",
            "query", "prompt", "diagnosis", "recommendations", "confidence", "stack",
        ):
            self.assertNotIn(forbidden, serialized.lower())

    async def test_keyless_writer_exchanges_oidc_and_writes_allowlist(self) -> None:
        seen: list[httpx.Request] = []

        def handler(incoming: httpx.Request) -> httpx.Response:
            seen.append(incoming)
            if incoming.url.host == "sts.googleapis.com":
                return httpx.Response(200, json={"access_token": "federated"}, request=incoming)
            if incoming.url.host == "iamcredentials.googleapis.com":
                return httpx.Response(200, json={"accessToken": "short-lived"}, request=incoming)
            return httpx.Response(200, json={}, request=incoming)

        event = build_audit_event(
            request_with_headers({"x-vercel-forwarded-for": "198.51.100.7"}),
            self.audit_settings(),
            "access_verify",
            200,
            str(uuid4()),
        )
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            await CloudAuditWriter(self.audit_settings(), client).write(event, "vercel-oidc")

        self.assertEqual([item.url.host for item in seen], [
            "sts.googleapis.com", "iamcredentials.googleapis.com", "logging.googleapis.com",
        ])
        sts_payload = json.loads(seen[0].content)
        self.assertEqual(sts_payload["subjectToken"], "vercel-oidc")
        self.assertIn("/providers/farm-scout-production", sts_payload["audience"])
        log_payload = json.loads(seen[2].content)
        self.assertEqual(log_payload["entries"], [{"jsonPayload": event.to_payload()}])
        self.assertNotIn("vercel-oidc", seen[2].content.decode())


class AuditMiddlewareTests(unittest.TestCase):
    def setUp(self) -> None:
        self.previous_writer = app.state.audit_writer
        self.previous_access_code = settings.demo_access_code
        self.previous_vercel = settings.vercel
        self.previous_vercel_env = settings.vercel_env
        settings.demo_access_code = "correct-code"
        settings.vercel = "1"
        settings.vercel_env = "production"

    def tearDown(self) -> None:
        app.state.audit_writer = self.previous_writer
        settings.demo_access_code = self.previous_access_code
        settings.vercel = self.previous_vercel
        settings.vercel_env = self.previous_vercel_env

    def client(self) -> TestClient:
        return TestClient(app, raise_server_exceptions=False)

    def test_access_success_401_and_audit_failure_preserves_response(self) -> None:
        writer = CapturingWriter()
        app.state.audit_writer = writer
        with self.client() as client:
            success = client.get(
                "/access/verify",
                headers={
                    "X-Demo-Access-Code": "correct-code",
                    "x-vercel-forwarded-for": "198.51.100.8",
                    "x-vercel-oidc-token": "opaque-token",
                },
            )
            denied = client.get("/access/verify", headers={"X-Demo-Access-Code": "wrong"})
        self.assertEqual(success.status_code, 200)
        self.assertEqual(denied.status_code, 401)
        self.assertEqual(len(writer.events), 2)
        self.assertEqual(writer.events[0].outcome, "succeeded")
        self.assertEqual(writer.events[1].error_category, "auth_failed")

        failing_writer = CapturingWriter(fail=True)
        app.state.audit_writer = failing_writer
        with self.client() as client:
            unaffected = client.get("/access/verify", headers={"X-Demo-Access-Code": "correct-code"})
        self.assertEqual(unaffected.status_code, 200)
        self.assertEqual(len(failing_writer.events), 1)

    def test_scan_validation_success_and_provider_failure_each_emit_once(self) -> None:
        writer = CapturingWriter()
        app.state.audit_writer = writer
        valid_request = {
            "imageBase64": "/9j/2Q==",
            "imageMimeType": "image/jpeg",
            "provider": "gemini",
            "language": "en",
        }
        with patch("app.main.get_ai_provider", return_value=FakeProvider()), patch(
            "app.main.SupabaseScanStore", FakeStore
        ):
            with self.client() as client:
                validation = client.post(
                    "/api/scans/analyze",
                    headers={"X-Demo-Access-Code": "correct-code"},
                    json={**valid_request, "provider": "unsupported"},
                )
                success = client.post(
                    "/api/scans/analyze",
                    headers={"X-Demo-Access-Code": "correct-code"},
                    json=valid_request,
                )
        self.assertEqual(validation.status_code, 422)
        self.assertEqual(success.status_code, 200)
        self.assertEqual(len(writer.events), 2)
        self.assertEqual(writer.events[0].error_category, "validation_failed")
        self.assertEqual(writer.events[1].provider, "gemini")
        self.assertEqual(writer.events[1].provider_outcome, "succeeded")

        writer.events.clear()
        with patch(
            "app.main.get_ai_provider",
            return_value=FakeProvider(httpx.ReadTimeout("synthetic timeout")),
        ):
            with self.client() as client:
                failed = client.post(
                    "/api/scans/analyze",
                    headers={"X-Demo-Access-Code": "correct-code"},
                    json=valid_request,
                )
        self.assertEqual(failed.status_code, 502)
        self.assertEqual(len(writer.events), 1)
        self.assertEqual(writer.events[0].provider_outcome, "failed")
        self.assertEqual(writer.events[0].error_category, "provider_timeout")

    def test_prototype_is_audited_as_an_external_provider(self) -> None:
        writer = CapturingWriter()
        app.state.audit_writer = writer
        with patch("app.main.get_ai_provider", return_value=FakeProvider()), patch(
            "app.main.SupabaseScanStore", FakeStore
        ):
            with self.client() as client:
                response = client.post(
                    "/api/scans/analyze",
                    headers={"X-Demo-Access-Code": "correct-code"},
                    json={
                        "imageBase64": "/9j/2Q==",
                        "imageMimeType": "image/jpeg",
                        "provider": "prototype",
                        "language": "en",
                    },
                )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(writer.events), 1)
        self.assertTrue(writer.events[0].external_api_used)
        self.assertEqual(writer.events[0].provider, "prototype")
        self.assertEqual(writer.events[0].provider_outcome, "succeeded")

    def test_scan_persistence_failure_emits_one_sanitized_category(self) -> None:
        writer = CapturingWriter()
        app.state.audit_writer = writer
        with patch("app.main.get_ai_provider", return_value=FakeProvider()), patch(
            "app.main.SupabaseScanStore", FailingStore
        ):
            with self.client() as client:
                response = client.post(
                    "/api/scans/analyze",
                    headers={"X-Demo-Access-Code": "correct-code"},
                    json={
                        "imageBase64": "/9j/2Q==",
                        "imageMimeType": "image/jpeg",
                        "provider": "gemini",
                        "language": "en",
                    },
                )
        self.assertEqual(response.status_code, 503)
        self.assertEqual(len(writer.events), 1)
        self.assertEqual(writer.events[0].provider_outcome, "succeeded")
        self.assertEqual(writer.events[0].error_category, "persistence_failed")


if __name__ == "__main__":
    unittest.main()

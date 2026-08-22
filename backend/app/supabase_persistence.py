import base64
import binascii
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote, urljoin, urlsplit
from uuid import UUID, uuid4

import httpx

from app.config import Settings
from app.schemas import (
    AnalyzeScanRequest,
    AnalyzeScanResponse,
    PersistedAnalyzeScanResponse,
    RecentScan,
    ScanDetail,
)


class PersistenceError(RuntimeError):
    pass


class ScanNotFoundError(PersistenceError):
    pass


class SupabaseScanStore:
    def __init__(self, settings: Settings, client: httpx.AsyncClient | None = None):
        if not settings.supabase_url or not settings.supabase_service_role_key:
            raise PersistenceError("Supabase persistence is not configured")
        self.base_url = settings.supabase_url.rstrip("/")
        self.api_key = settings.supabase_service_role_key
        self.bucket = settings.supabase_storage_bucket
        self.signed_url_ttl_seconds = settings.supabase_signed_url_ttl_seconds
        self._client = client

    def _headers(self, **extra: str) -> dict[str, str]:
        headers = {"apikey": self.api_key, **extra}
        # New sb_secret keys must only use apikey. Legacy service_role JWTs also
        # need Authorization for direct PostgREST/Storage compatibility.
        if not self.api_key.startswith("sb_secret_"):
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def _request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        try:
            if self._client:
                return await self._client.request(method, url, **kwargs)
            async with httpx.AsyncClient(timeout=30) as client:
                return await client.request(method, url, **kwargs)
        except httpx.HTTPError as exc:
            raise PersistenceError("Supabase request failed") from exc

    async def persist_success(
        self,
        request: AnalyzeScanRequest,
        analysis: AnalyzeScanResponse,
        model_name: str | None,
    ) -> PersistedAnalyzeScanResponse:
        if request.image_mime_type != "image/jpeg" or not request.image_base64:
            raise PersistenceError("A compressed JPEG is required for persistence")
        try:
            image_bytes = base64.b64decode(request.image_base64, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise PersistenceError("The submitted JPEG is not valid base64") from exc
        if not image_bytes or len(image_bytes) > 5_000_000:
            raise PersistenceError("The submitted JPEG is empty or exceeds the storage limit")
        if not image_bytes.startswith(b"\xff\xd8") or not image_bytes.endswith(b"\xff\xd9"):
            raise PersistenceError("The submitted image is not a JPEG")

        scan_id = uuid4()
        created_at = datetime.now(timezone.utc)
        object_path = f"demo/{created_at:%Y/%m/%d}/{scan_id}.jpg"
        await self._upload_image(object_path, image_bytes)

        analysis_json = analysis.model_dump(mode="json")
        row = {
            "id": str(scan_id),
            "image_path": object_path,
            "ai_provider": request.provider,
            "language": request.language,
            "stress_level": analysis.stress_level,
            "severity_score": analysis.severity_score,
            "confidence": analysis.confidence,
            "diagnosis": analysis.diagnosis,
            "detected_issues": analysis.detected_issues,
            "recommendations": analysis.recommendations,
            "needs_human_review": analysis.needs_human_review,
            "status": "succeeded",
            "data_stage": "demo",
            "data_purpose": "user_upload",
            "image_mime_type": "image/jpeg",
            "image_size_bytes": len(image_bytes),
            "location_snapshot": request.location_snapshot,
            "analysis_result": analysis_json,
            "analysis_schema_version": "1",
            "model_name": model_name,
            "created_at": created_at.isoformat(),
        }
        try:
            await self._insert_scan(row)
        except Exception as exc:
            try:
                await self._delete_image(object_path)
            except Exception as cleanup_exc:
                raise PersistenceError(
                    "Scan row insert failed and image compensation also failed"
                ) from cleanup_exc
            if isinstance(exc, PersistenceError):
                raise
            raise PersistenceError("Scan row insert failed") from exc

        return PersistedAnalyzeScanResponse(
            **analysis_json,
            scan_id=scan_id,
            created_at=created_at,
        )

    async def list_recent(self, limit: int = 10) -> list[RecentScan]:
        response = await self._request(
            "GET",
            f"{self.base_url}/rest/v1/scans",
            headers=self._headers(),
            params={
                "select": "id,created_at,stress_level,severity_score,confidence,diagnosis,location_snapshot",
                "data_stage": "eq.demo",
                "data_purpose": "eq.user_upload",
                "status": "eq.succeeded",
                "order": "created_at.desc",
                "limit": str(min(limit, 10)),
            },
        )
        self._raise_for_status(response, "Recent scans query failed")
        try:
            return [RecentScan.model_validate(item) for item in response.json()]
        except (TypeError, ValueError) as exc:
            raise PersistenceError("Recent scans returned invalid data") from exc

    async def get_detail(self, scan_id: UUID) -> ScanDetail:
        response = await self._request(
            "GET",
            f"{self.base_url}/rest/v1/scans",
            headers=self._headers(),
            params={
                "select": "id,created_at,stress_level,severity_score,confidence,diagnosis,location_snapshot,analysis_result,image_path",
                "id": f"eq.{scan_id}",
                "data_stage": "eq.demo",
                "data_purpose": "eq.user_upload",
                "status": "eq.succeeded",
                "limit": "1",
            },
        )
        self._raise_for_status(response, "Scan detail query failed")
        try:
            rows = response.json()
        except ValueError as exc:
            raise PersistenceError("Scan detail returned invalid data") from exc
        if not rows:
            raise ScanNotFoundError("Scan not found")
        try:
            row = rows[0]
            image_path = row.pop("image_path")
            image_url = await self._create_signed_url(image_path)
            return ScanDetail.model_validate({**row, "image_url": image_url})
        except (KeyError, TypeError, ValueError) as exc:
            raise PersistenceError("Scan detail returned invalid data") from exc

    async def _upload_image(self, object_path: str, image_bytes: bytes) -> None:
        encoded_path = quote(object_path, safe="/")
        response = await self._request(
            "POST",
            f"{self.base_url}/storage/v1/object/{self.bucket}/{encoded_path}",
            headers=self._headers(
                **{"Content-Type": "image/jpeg", "x-upsert": "false"}
            ),
            content=image_bytes,
        )
        self._raise_for_status(response, "Scan image upload failed")

    async def _insert_scan(self, row: dict[str, Any]) -> None:
        response = await self._request(
            "POST",
            f"{self.base_url}/rest/v1/scans",
            headers=self._headers(
                **{"Content-Type": "application/json", "Prefer": "return=minimal"}
            ),
            json=row,
        )
        self._raise_for_status(response, "Scan row insert failed")

    async def _delete_image(self, object_path: str) -> None:
        encoded_path = quote(object_path, safe="/")
        response = await self._request(
            "DELETE",
            f"{self.base_url}/storage/v1/object/{self.bucket}/{encoded_path}",
            headers=self._headers(),
        )
        self._raise_for_status(response, "Scan image compensation failed")

    async def _create_signed_url(self, object_path: str) -> str:
        encoded_path = quote(object_path, safe="/")
        response = await self._request(
            "POST",
            f"{self.base_url}/storage/v1/object/sign/{self.bucket}/{encoded_path}",
            headers=self._headers(**{"Content-Type": "application/json"}),
            json={"expiresIn": self.signed_url_ttl_seconds},
        )
        self._raise_for_status(response, "Signed image URL creation failed")
        try:
            payload = response.json()
            signed_path = payload.get("signedURL") or payload.get("signedUrl")
        except (AttributeError, ValueError) as exc:
            raise PersistenceError("Signed image URL creation returned invalid data") from exc
        if not signed_path:
            raise PersistenceError("Signed image URL creation returned no URL")
        if not isinstance(signed_path, str):
            raise PersistenceError("Signed image URL creation returned invalid data")

        parsed = urlsplit(signed_path)
        if parsed.scheme and parsed.netloc:
            return signed_path

        normalized_path = signed_path.lstrip("/")
        if normalized_path.startswith("object/"):
            normalized_path = f"storage/v1/{normalized_path}"
        return urljoin(f"{self.base_url}/", normalized_path)

    @staticmethod
    def _raise_for_status(response: httpx.Response, message: str) -> None:
        if response.is_error:
            raise PersistenceError(f"{message} ({response.status_code})")

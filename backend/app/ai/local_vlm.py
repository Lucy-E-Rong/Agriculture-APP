import httpx
from app.ai.base import AiProviderClient
from app.config import Settings
from app.schemas import AnalyzeScanRequest, AnalyzeScanResponse


class LocalVlmProvider(AiProviderClient):
    def __init__(self, settings: Settings):
        self.settings = settings

    async def analyze(self, request: AnalyzeScanRequest) -> AnalyzeScanResponse:
        headers = {}
        if self.settings.local_vlm_api_key:
            headers["Authorization"] = f"Bearer {self.settings.local_vlm_api_key}"

        payload = {
            "image_base64": request.image_base64,
            "image_uri": request.image_uri,
            "language": request.language,
            "crop_id": request.crop_id,
            "greenhouse_id": request.greenhouse_id,
            "section_id": request.section_id,
            "table_id": request.table_id,
            "row_id": request.row_id,
            "response_schema": {
                "stress_level": "none|low|medium|high|critical",
                "severity_score": "integer 0-5",
                "confidence": "float 0-1",
                "diagnosis": "string",
                "detected_issues": "string[]",
                "recommendations": "string[]",
                "needs_human_review": "boolean",
            },
        }

        async with httpx.AsyncClient(timeout=90) as client:
            response = await client.post(self.settings.local_vlm_url, json=payload, headers=headers)
            response.raise_for_status()
            return AnalyzeScanResponse.model_validate(response.json())


import httpx
from app.ai.base import AiProviderClient
from app.ai.mock_provider import MockProvider
from app.config import Settings
from app.schemas import AnalyzeScanRequest, AnalyzeScanResponse


class ApiProvider(AiProviderClient):
    def __init__(self, settings: Settings):
        self.settings = settings
        self.mock = MockProvider()

    async def analyze(self, request: AnalyzeScanRequest) -> AnalyzeScanResponse:
        if self.settings.openai_api_key:
            return await self._analyze_with_openai(request)

        if self.settings.anthropic_api_key:
            return await self._analyze_with_anthropic(request)

        return await self.mock.analyze(request)

    async def _analyze_with_openai(self, request: AnalyzeScanRequest) -> AnalyzeScanResponse:
        prompt = build_prompt(request)
        content = [{"type": "text", "text": prompt}]
        if request.image_base64:
            content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{request.image_base64}"}})

        payload = {
            "model": self.settings.openai_model,
            "messages": [{"role": "user", "content": content}],
            "response_format": {"type": "json_object"},
        }
        headers = {"Authorization": f"Bearer {self.settings.openai_api_key}"}

        async with httpx.AsyncClient(timeout=90) as client:
            response = await client.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            text = data["choices"][0]["message"]["content"]
            return AnalyzeScanResponse.model_validate_json(text)

    async def _analyze_with_anthropic(self, request: AnalyzeScanRequest) -> AnalyzeScanResponse:
        prompt = build_prompt(request)
        content = [{"type": "text", "text": prompt}]
        if request.image_base64:
            content.append({
                "type": "image",
                "source": {"type": "base64", "media_type": "image/jpeg", "data": request.image_base64},
            })

        payload = {
            "model": self.settings.anthropic_model,
            "max_tokens": 1200,
            "messages": [{"role": "user", "content": content}],
        }
        headers = {
            "x-api-key": self.settings.anthropic_api_key or "",
            "anthropic-version": "2023-06-01",
        }

        async with httpx.AsyncClient(timeout=90) as client:
            response = await client.post("https://api.anthropic.com/v1/messages", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            text = data["content"][0]["text"]
            return AnalyzeScanResponse.model_validate_json(text)


def build_prompt(request: AnalyzeScanRequest) -> str:
    language_name = "Simplified Chinese" if request.language == "zh" else "English"
    return f"""
You are FarmScout, an agricultural image analysis assistant.
Analyze the crop image and return only valid JSON.
Use {language_name} for diagnosis and recommendations.

Context:
- crop_id: {request.crop_id}
- greenhouse_id: {request.greenhouse_id}
- section_id: {request.section_id}
- table_id: {request.table_id}
- row_id: {request.row_id}

Return exactly this JSON shape:
{{
  "stress_level": "none|low|medium|high|critical",
  "severity_score": 0,
  "confidence": 0.0,
  "diagnosis": "string",
  "detected_issues": ["string"],
  "recommendations": ["string"],
  "needs_human_review": false
}}
""".strip()


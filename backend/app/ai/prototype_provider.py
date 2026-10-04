import httpx

from app.ai.base import AiProviderClient
from app.config import Settings
from app.schemas import AnalyzeScanRequest, PrototypeAnalysisResponse


PROTOTYPE_TASK = (
    "Does it show signs of water stress? Tell me what you notice, how severe "
    "it looks, and what I should check or do next."
)

PROTOTYPE_PROMPT = PROTOTYPE_TASK


class PrototypeNotConfiguredError(RuntimeError):
    pass


class PrototypeProvider(AiProviderClient):
    def __init__(self, settings: Settings):
        self.settings = settings

    async def analyze(self, request: AnalyzeScanRequest) -> PrototypeAnalysisResponse:
        prompt = build_prototype_prompt(request)
        if not prompt:
            raise PrototypeNotConfiguredError("Prototype is not configured")
        if not self.settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured")
        if not request.image_base64:
            raise ValueError("Prototype analysis requires imageBase64")

        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.settings.gemini_model}:generateContent"
        )
        payload = {
            "contents": [{
                "role": "user",
                "parts": [
                    {"text": prompt},
                    {
                        "inlineData": {
                            "mimeType": request.image_mime_type,
                            "data": request.image_base64,
                        }
                    },
                ],
            }],
            "generationConfig": {
                "temperature": 0.15,
            },
        }

        async with httpx.AsyncClient(timeout=90) as client:
            response = await client.post(
                url,
                json=payload,
                headers={"x-goog-api-key": self.settings.gemini_api_key},
            )
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                try:
                    message = response.json().get("error", {}).get(
                        "message", "Unknown Gemini API error"
                    )
                except ValueError:
                    message = "Unknown Gemini API error"
                raise RuntimeError(
                    f"Prototype API rejected the request: {message}"
                ) from exc
            data = response.json()

        try:
            text = data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError) as exc:
            block_reason = data.get("promptFeedback", {}).get("blockReason", "unknown")
            raise RuntimeError(
                f"Prototype returned no analysis (block reason: {block_reason})"
            ) from exc

        if not isinstance(text, str) or not text.strip():
            raise RuntimeError("Prototype returned an empty text response")
        return PrototypeAnalysisResponse(response_text=text.strip())


def build_prototype_prompt(request: AnalyzeScanRequest) -> str:
    del request
    return PROTOTYPE_PROMPT.strip()

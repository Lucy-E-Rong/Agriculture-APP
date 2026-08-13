import json

import httpx

from app.ai.base import AiProviderClient
from app.config import Settings
from app.schemas import AnalyzeScanRequest, AnalyzeScanResponse


class GeminiProvider(AiProviderClient):
    def __init__(self, settings: Settings):
        self.settings = settings

    async def analyze(self, request: AnalyzeScanRequest) -> AnalyzeScanResponse:
        if not self.settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured")
        if not request.image_base64:
            raise ValueError("Gemini analysis requires imageBase64")

        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.settings.gemini_model}:generateContent"
        )
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": build_prompt(request)},
                        {
                            "inlineData": {
                                "mimeType": request.image_mime_type,
                                "data": request.image_base64,
                            }
                        },
                    ],
                }
            ],
            "generationConfig": {
                "temperature": 0.15,
                "responseMimeType": "application/json",
                "responseJsonSchema": gemini_response_schema(),
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
                    message = response.json().get("error", {}).get("message", "Unknown Gemini API error")
                except ValueError:
                    message = "Unknown Gemini API error"
                raise RuntimeError(f"Gemini API rejected the request: {message}") from exc
            data = response.json()

        try:
            text = data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError) as exc:
            block_reason = data.get("promptFeedback", {}).get("blockReason", "unknown")
            raise RuntimeError(f"Gemini returned no analysis (block reason: {block_reason})") from exc

        try:
            return AnalyzeScanResponse.model_validate(json.loads(text))
        except (json.JSONDecodeError, ValueError) as exc:
            raise RuntimeError("Gemini returned an invalid structured response") from exc


def build_prompt(request: AnalyzeScanRequest) -> str:
    output_language = "Simplified Chinese" if request.language == "zh" else "English"
    return f"""
You are the visual inspection component of FarmScout, an AI-assisted crop
monitoring system. Inspect this smartphone image for EARLY VISIBLE signs of
stress in lettuce and return the assessment in {output_language}.

Follow this protocol:
1. Decide whether lettuce is visible and estimate crop confidence.
2. Check whether the image is usable. Consider blur, darkness, distance,
   occlusion, and whether enough leaf area is visible. If unusable, set
   image_quality.usable=false, provide retake guidance, set
   plant_stress_detected=false and do not invent symptoms or causes.
3. Record only directly observable symptoms, such as discoloration, chlorosis,
   wilting, curling, spotting, lesions, necrosis, edge browning, physical damage,
   abnormal growth, or visible pest damage.
4. Assess severity from none to critical.
5. Keep possible causes separate from observed facts. Never claim a specific
   disease, pathogen, nutrient deficiency, or invisible physiological condition
   unless the image provides strong distinguishing evidence.
6. When evidence is ambiguous, lower confidence and say it is uncertain.
7. Recommend safe field checks, not pesticide applications or fertilizer doses.
8. detected_issues must contain short machine-readable symptom labels.

Location context (identifiers may be absent):
- crop_id: {request.crop_id}
- greenhouse_id: {request.greenhouse_id}
- section_id: {request.section_id}
- table_id: {request.table_id}
- row_id: {request.row_id}

Return only JSON matching the supplied schema. Do not use Markdown.
""".strip()


def gemini_response_schema() -> dict:
    string_array = {"type": "array", "items": {"type": "string"}}
    return {
        "type": "object",
        "properties": {
            "crop_is_lettuce": {"type": "boolean"},
            "crop_confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "image_quality": {
                "type": "object",
                "properties": {
                    "usable": {"type": "boolean"},
                    "issues": string_array,
                    "retake_guidance": string_array,
                },
                "required": ["usable", "issues", "retake_guidance"],
            },
            "plant_stress_detected": {"type": "boolean"},
            "stress_level": {
                "type": "string",
                "enum": ["none", "low", "medium", "high", "critical"],
            },
            "severity_score": {"type": "integer", "minimum": 0, "maximum": 5},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "diagnosis": {"type": "string"},
            "observed_symptoms": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string"},
                        "location": {"type": "string"},
                        "description": {"type": "string"},
                    },
                    "required": ["type", "location", "description"],
                },
            },
            "possible_causes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "category": {"type": "string"},
                        "likelihood": {
                            "type": "string",
                            "enum": ["uncertain", "possible", "likely"],
                        },
                        "reason": {"type": "string"},
                    },
                    "required": ["category", "likelihood", "reason"],
                },
            },
            "detected_issues": string_array,
            "recommendations": string_array,
            "needs_human_review": {"type": "boolean"},
        },
        "required": [
            "crop_is_lettuce",
            "crop_confidence",
            "image_quality",
            "plant_stress_detected",
            "stress_level",
            "severity_score",
            "confidence",
            "diagnosis",
            "observed_symptoms",
            "possible_causes",
            "detected_issues",
            "recommendations",
            "needs_human_review",
        ],
    }

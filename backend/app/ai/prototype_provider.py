import json

import httpx

from app.ai.base import AiProviderClient
from app.config import Settings
from app.schemas import AnalyzeScanRequest, AnalyzeScanResponse


PROTOTYPE_TASK = (
    "Does it show signs of water stress? Tell me what you notice, how severe "
    "it looks, and what I should check or do next."
)

# The first sentence is the complete A-group task. Everything after it is a
# neutral serialization instruction required by the existing online response
# contract; it deliberately contains no FarmScout assessment protocol.
PROTOTYPE_PROMPT = f"""
{PROTOTYPE_TASK}

Return only JSON matching the supplied schema, with every required field present
and no extra fields. Use ordinary visual judgment to fill the fields. Keep text
and arrays concise. Do not use Markdown. If needs_human_review is false,
human_review_reasons must be an empty array.
""".strip()


class PrototypeNotConfiguredError(RuntimeError):
    pass


class PrototypeProvider(AiProviderClient):
    def __init__(self, settings: Settings):
        self.settings = settings

    async def analyze(self, request: AnalyzeScanRequest) -> AnalyzeScanResponse:
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
                "responseMimeType": "application/json",
                "responseJsonSchema": prototype_response_schema(),
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

        try:
            return AnalyzeScanResponse.model_validate(json.loads(text))
        except (json.JSONDecodeError, ValueError) as exc:
            raise RuntimeError("Prototype returned an invalid structured response") from exc


def build_prototype_prompt(request: AnalyzeScanRequest) -> str:
    del request
    return PROTOTYPE_PROMPT.strip()


def prototype_response_schema() -> dict:
    string_array = {"type": "array", "items": {"type": "string"}}
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "crop_is_lettuce": {"type": "boolean"},
            "crop_confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "image_quality": {
                "type": "object",
                "additionalProperties": False,
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
                    "additionalProperties": False,
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
                    "additionalProperties": False,
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
            "human_review_reasons": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": [
                        "high_or_critical_water_stress",
                        "non_water_factor_to_rule_out",
                        "ambiguous_visual_evidence",
                    ],
                },
            },
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
            "human_review_reasons",
        ],
    }

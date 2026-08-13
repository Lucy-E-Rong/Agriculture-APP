from typing import Literal
from pydantic import BaseModel, Field, model_validator

AiProvider = Literal["gemini", "api_provider", "local_vlm", "mock"]
Language = Literal["en", "zh"]
StressLevel = Literal["none", "low", "medium", "high", "critical"]
CauseLikelihood = Literal["uncertain", "possible", "likely"]


class ImageQuality(BaseModel):
    usable: bool = True
    issues: list[str] = Field(default_factory=list)
    retake_guidance: list[str] = Field(default_factory=list)


class ObservedSymptom(BaseModel):
    type: str
    location: str
    description: str


class PossibleCause(BaseModel):
    category: str
    likelihood: CauseLikelihood
    reason: str


class AnalyzeScanRequest(BaseModel):
    image_base64: str | None = None
    image_uri: str | None = None
    image_mime_type: str = "image/jpeg"
    provider: AiProvider = "gemini"
    language: Language = "en"
    crop_id: str | None = None
    greenhouse_id: str | None = None
    section_id: str | None = None
    table_id: str | None = None
    row_id: str | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_camel_case(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data
        key_map = {
            "imageBase64": "image_base64",
            "imageUri": "image_uri",
            "imageMimeType": "image_mime_type",
            "cropId": "crop_id",
            "greenhouseId": "greenhouse_id",
            "sectionId": "section_id",
            "tableId": "table_id",
            "rowId": "row_id",
        }
        normalized = dict(data)
        for camel_key, snake_key in key_map.items():
            if camel_key in normalized and snake_key not in normalized:
                normalized[snake_key] = normalized.pop(camel_key)
        return normalized


class AnalyzeScanResponse(BaseModel):
    crop_is_lettuce: bool = True
    crop_confidence: float = Field(default=1, ge=0, le=1)
    image_quality: ImageQuality = Field(default_factory=ImageQuality)
    plant_stress_detected: bool = True
    stress_level: StressLevel
    severity_score: int = Field(ge=0, le=5)
    confidence: float = Field(ge=0, le=1)
    diagnosis: str
    observed_symptoms: list[ObservedSymptom] = Field(default_factory=list)
    possible_causes: list[PossibleCause] = Field(default_factory=list)
    detected_issues: list[str]
    recommendations: list[str]
    needs_human_review: bool


class HealthResponse(BaseModel):
    status: str
    app_env: str
    gemini_configured: bool
    gemini_model: str

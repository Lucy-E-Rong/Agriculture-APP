from datetime import datetime
from typing import Any, Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

AiProvider = Literal["gemini", "prototype", "api_provider", "local_vlm", "mock"]
AiModel = Literal["gemini-3.6-flash", "gpt-5.6-terra"]
Language = Literal["en", "zh"]
StressLevel = Literal["none", "low", "medium", "high", "critical"]
CauseLikelihood = Literal["uncertain", "possible", "likely"]
HumanReviewReason = Literal[
    "high_or_critical_water_stress",
    "non_water_factor_to_rule_out",
    "ambiguous_visual_evidence",
]


class ScanLocationSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display: str | None = Field(default=None, max_length=500)
    greenhouse: str | None = Field(default=None, max_length=120)
    section: str | None = Field(default=None, max_length=120)
    table: str | None = Field(default=None, max_length=120)
    row: str | None = Field(default=None, max_length=120)
    plant_id: str | None = Field(default=None, max_length=120)
    sample_id: str | None = Field(default=None, max_length=120)
    variety: str | None = Field(default=None, max_length=120)
    period: str | None = Field(default=None, max_length=120)
    # Kept for reading and validating 0.3.0-era snapshots.
    growth_stage: str | None = Field(default=None, max_length=120)

    @field_validator("*", mode="before")
    @classmethod
    def trim_optional_strings(cls, value: object) -> object:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("scan context values must be strings")
        trimmed = value.strip()
        return trimmed or None


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
    model_id: AiModel = "gemini-3.6-flash"
    language: Language = "en"
    crop_id: str | None = None
    greenhouse_id: str | None = None
    section_id: str | None = None
    table_id: str | None = None
    row_id: str | None = None
    location_snapshot: ScanLocationSnapshot = Field(default_factory=ScanLocationSnapshot)

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
            "locationSnapshot": "location_snapshot",
            "modelId": "model_id",
        }
        normalized = dict(data)
        for camel_key, snake_key in key_map.items():
            if camel_key in normalized and snake_key not in normalized:
                normalized[snake_key] = normalized.pop(camel_key)
        return normalized


class AnalyzeScanResponse(BaseModel):
    response_kind: Literal["farmscout"] = "farmscout"
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
    human_review_reasons: list[HumanReviewReason] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_human_review_shape(self) -> "AnalyzeScanResponse":
        if not self.needs_human_review and self.human_review_reasons:
            raise ValueError("human_review_reasons must be empty when human review is false")
        if len(self.human_review_reasons) != len(set(self.human_review_reasons)):
            raise ValueError("human_review_reasons must not contain duplicates")
        return self


class PersistedAnalyzeScanResponse(AnalyzeScanResponse):
    scan_id: UUID
    created_at: datetime


class PrototypeAnalysisResponse(BaseModel):
    """An ordinary free-text answer from the unstructured Prototype arm."""

    response_kind: Literal["prototype"] = "prototype"
    response_text: str = Field(min_length=1)


class PersistedPrototypeAnalysisResponse(PrototypeAnalysisResponse):
    scan_id: UUID
    created_at: datetime


AnalysisResponse = AnalyzeScanResponse | PrototypeAnalysisResponse
PersistedAnalysisResponse = PersistedAnalyzeScanResponse | PersistedPrototypeAnalysisResponse
AnalyzeEndpointResponse = PersistedAnalysisResponse | AnalysisResponse


class RecentScan(BaseModel):
    id: UUID
    created_at: datetime
    ai_provider: AiProvider = "gemini"
    model_name: str | None = None
    stress_level: StressLevel | None = None
    severity_score: int | None = Field(default=None, ge=0, le=5)
    confidence: float | None = Field(default=None, ge=0, le=1)
    diagnosis: str | None = None
    location_snapshot: dict[str, Any] = Field(default_factory=dict)


class ScanDetail(RecentScan):
    analysis_result: AnalysisResponse
    image_url: str


class HealthResponse(BaseModel):
    status: str
    app_env: str
    gemini_configured: bool
    gemini_model: str

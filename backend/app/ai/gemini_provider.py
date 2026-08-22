import json

import httpx

from app.ai.base import AiProviderClient
from app.config import Settings
from app.schemas import AnalyzeScanRequest, AnalyzeScanResponse


WATER_SOURCE_CATEGORIES = [
    "water_availability_to_check",
    "irrigation_delivery_to_check",
    "root_zone_moisture_to_check",
    "transpiration_demand_to_check",
]
NON_WATER_EXCLUSION_CATEGORIES = [
    "disease_to_rule_out",
    "pest_to_rule_out",
    "nutrient_or_physiological_to_rule_out",
    "physical_damage_to_rule_out",
]
HUMAN_REVIEW_REASONS = [
    "high_or_critical_water_stress",
    "non_water_factor_to_rule_out",
    "ambiguous_visual_evidence",
]


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
            result = AnalyzeScanResponse.model_validate(json.loads(text))
            validate_water_stress_contract(result)
            validate_human_review_decision(result)
            return result
        except (json.JSONDecodeError, ValueError) as exc:
            raise RuntimeError("Gemini returned an invalid structured response") from exc


def validate_water_stress_contract(result: AnalyzeScanResponse) -> None:
    expected_level = {
        0: "none",
        1: "low",
        2: "low",
        3: "medium",
        4: "high",
        5: "critical",
    }[result.severity_score]
    if result.stress_level != expected_level:
        raise ValueError("stress_level does not match severity_score")

    blocked_assessment = not result.image_quality.usable or not result.crop_is_lettuce
    if blocked_assessment and (
        result.severity_score != 0
        or result.plant_stress_detected
        or result.observed_symptoms
        or result.possible_causes
        or result.detected_issues
    ):
        raise ValueError("an unusable or non-lettuce image cannot assert plant stress")

    if result.severity_score > 0 and (
        not result.plant_stress_detected or not result.observed_symptoms
    ):
        raise ValueError("visible water stress requires observable symptoms")

    if result.possible_causes and not result.observed_symptoms:
        raise ValueError("possible causes require observable symptoms")

    allowed_categories = set(WATER_SOURCE_CATEGORIES + NON_WATER_EXCLUSION_CATEGORIES)
    if any(cause.category not in allowed_categories for cause in result.possible_causes):
        raise ValueError("possible cause category is outside the water-stress contract")


def validate_human_review_decision(result: AnalyzeScanResponse) -> None:
    required_reasons: set[str] = set()
    if result.severity_score >= 4:
        required_reasons.add("high_or_critical_water_stress")
    if any(
        cause.category in NON_WATER_EXCLUSION_CATEGORIES
        for cause in result.possible_causes
    ):
        required_reasons.add("non_water_factor_to_rule_out")

    actual_reasons = set(result.human_review_reasons)
    if required_reasons - actual_reasons:
        raise ValueError("human review is missing one or more required reasons")
    if actual_reasons and not result.needs_human_review:
        raise ValueError("human review reasons require human review")
    if result.needs_human_review and not actual_reasons:
        raise ValueError("human review requires at least one reason")
    allowed_actual_reasons = required_reasons | {"ambiguous_visual_evidence"}
    if actual_reasons - allowed_actual_reasons:
        raise ValueError("human review includes a reason without its trigger")
    if not required_reasons and result.needs_human_review:
        if actual_reasons != {"ambiguous_visual_evidence"}:
            raise ValueError("human review is not justified by an allowed trigger")
    if required_reasons and not result.needs_human_review:
        raise ValueError("a required human-review trigger cannot be ignored")


def build_prompt(request: AnalyzeScanRequest) -> str:
    output_language = "Simplified Chinese" if request.language == "zh" else "English"
    return f"""
You are the visual inspection component of FarmScout, an AI-assisted crop
monitoring system for greenhouse lettuce. Inspect this smartphone image for
EARLY VISIBLE signs that are consistent with WATER STRESS and return the
assessment in {output_language}. This is a cautious scouting assessment, not a
confirmed diagnosis.

Apply this protocol in order and return only the final JSON:

1. Crop and image gates
- Decide whether greenhouse lettuce is visible and set crop_confidence only for
  that crop-identification decision.
- Judge blur, exposure, distance, occlusion, and visible leaf area. If the image
  is unusable, still return the complete schema: use stress_level="none" and
  severity_score=0, set plant_stress_detected=false, leave observed_symptoms,
  possible_causes, and detected_issues empty, give concrete retake guidance, and
  set needs_human_review=false with an empty human_review_reasons array.
- If lettuce is not visible, also use none/0 without inventing plant evidence and
  give concrete guidance to submit a lettuce image, with needs_human_review=false
  and an empty human_review_reasons array. Do not emit null, unknown,
  "Unable to assess", or any extra status outside the supplied enums.

2. Visible evidence before interpretation
- observed_symptoms and detected_issues may contain only features directly
  visible in the pixels: wilting, loss of turgor, curling, discoloration,
  chlorosis, dry or browned margins, necrosis, spotting, lesions, holes, visible
  pests, mold-like growth, or physical injury.
- Keep symptom type/location as concise machine-readable English labels even
  when descriptions are in {output_language}. Do not put a disease, nutrient
  deficiency, irrigation failure, sensor reading, or invisible root condition in
  observed_symptoms.
- plant_stress_detected means that the image shows a visible pattern consistent
  with water stress. A visible non-water abnormality may be recorded while this
  boolean remains false and water-stress severity remains 0.

3. Fixed water-stress severity mapping
- 0 = none: no visible water-stress pattern.
- 1 = low: very mild or early visible water-stress pattern.
- 2 = low: visible low water-stress pattern.
- 3 = medium: clear moderate visible water-stress pattern.
- 4 = high: severe visible water-stress pattern.
- 5 = critical: extreme visible water-stress pattern with likely major crop loss.
- Use the matching stress_level exactly: 0 none, 1-2 low, 3 medium, 4 high,
  5 critical. Scores above 0 require at least one directly observed symptom.
- Describe the plant as Healthy only when severity_score=0 and there is no other
  visible abnormality. If holes, mold-like growth, lesions, pest damage, physical
  injury, or another abnormal sign is visible, record it and do not say Healthy,
  even when water-stress severity is 0.

4. Possible stress sources
- possible_causes are hypotheses, never observed facts. Water-related checks are
  primary and must use only these categories: water_availability_to_check,
  irrigation_delivery_to_check, root_zone_moisture_to_check, or
  transpiration_demand_to_check.
- A water source must be phrased as something to verify in the greenhouse. Do not
  claim that irrigation, substrate moisture, humidity, airflow, EC, temperature,
  or any sensor has a particular value unless that value was supplied.
- Disease, pests, nutrition/physiology, or physical damage may appear only when
  a directly visible sign supports them, and only as disease_to_rule_out,
  pest_to_rule_out, nutrient_or_physiological_to_rule_out, or
  physical_damage_to_rule_out. Explain which visible sign justifies ruling it
  out; never claim confirmation from one image.
- Each possible-cause reason must cite a corresponding observed symptom. Prefer
  uncertain or possible; use likely only with strong distinguishing visual
  evidence.

5. Greenhouse recommendations
- Recommend practical checks tied to the supplied greenhouse/section/table/row
  context when identifiers are present: compare nearby plants, inspect irrigation
  delivery, check substrate/root-zone moisture, review recent available
  greenhouse records, and rescan after an appropriate observation interval.
- Never invent sensor values or imply that FarmScout read a sensor. Do not give
  pesticide or fertilizer doses, chemical-treatment instructions, or directions
  to remove/destroy plants.

6. Confidence and human review
- confidence is confidence in the overall visible water-stress assessment, not
  crop identity. Lower it for weak image evidence or competing explanations.
- Set needs_human_review=true only for these triggers and list every applicable
  reason in human_review_reasons: severity 4-5 as
  high_or_critical_water_stress; any supported non-water factor as
  non_water_factor_to_rule_out; or genuinely conflicting or unclear visible
  evidence that would affect safe action as ambiguous_visual_evidence.
- Image usability, crop identity, crop_confidence, and confidence do not by
  themselves trigger human review. Use the retake or replacement-image guidance
  in section 1 when an image is unusable or does not show lettuce.
- If none of those triggers applies, needs_human_review=false and
  human_review_reasons must be an empty array. Never use human review merely as a
  generic disclaimer.

7. Output discipline
- Return every required field and no extra fields. Use only supplied enum values.
- Keep arrays concise, deduplicated, and ordered by visual importance.
- Use {output_language} for diagnosis, symptom descriptions, possible-cause
  reasons, recommendations, image-quality issues, and retake guidance.
- detected_issues must be short machine-readable English labels.

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
    possible_cause_categories = WATER_SOURCE_CATEGORIES + NON_WATER_EXCLUSION_CATEGORIES
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
                        "category": {
                            "type": "string",
                            "enum": possible_cause_categories,
                        },
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
                "items": {"type": "string", "enum": HUMAN_REVIEW_REASONS},
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

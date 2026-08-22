import unittest

from app.ai.gemini_provider import (
    build_prompt,
    gemini_response_schema,
    validate_human_review_decision,
    validate_water_stress_contract,
)
from app.ai.api_provider import build_prompt as build_api_provider_prompt
from app.ai.mock_provider import MockProvider
from app.schemas import AnalyzeScanRequest, AnalyzeScanResponse


def response(**overrides) -> AnalyzeScanResponse:
    payload = {
        "crop_is_lettuce": True,
        "crop_confidence": 0.96,
        "image_quality": {"usable": True, "issues": [], "retake_guidance": []},
        "plant_stress_detected": True,
        "stress_level": "low",
        "severity_score": 2,
        "confidence": 0.86,
        "diagnosis": "Visible wilting is consistent with water stress.",
        "observed_symptoms": [{
            "type": "wilting",
            "location": "outer_leaves",
            "description": "Outer leaves show visible loss of turgor.",
        }],
        "possible_causes": [{
            "category": "irrigation_delivery_to_check",
            "likelihood": "possible",
            "reason": "Visible wilting supports checking water delivery.",
        }],
        "detected_issues": ["wilting"],
        "recommendations": ["Check irrigation delivery in this row."],
        "needs_human_review": False,
        "human_review_reasons": [],
    }
    payload.update(overrides)
    return AnalyzeScanResponse.model_validate(payload)


class GeminiPromptTests(unittest.TestCase):
    def test_prompt_contains_approved_water_stress_protocol(self) -> None:
        prompt = build_prompt(AnalyzeScanRequest(language="zh", row_id="R1"))
        for required_text in (
            "EARLY VISIBLE signs that are consistent with WATER STRESS",
            "0 none, 1-2 low, 3 medium, 4 high",
            "Describe the plant as Healthy only",
            "disease_to_rule_out",
            "Never invent sensor values",
            "pesticide or fertilizer doses",
            "human_review_reasons must be an empty array",
            "row_id: R1",
            "Simplified Chinese",
        ):
            with self.subTest(required_text=required_text):
                self.assertIn(required_text, prompt)

    def test_response_schema_requires_review_reasons_and_closed_objects(self) -> None:
        schema = gemini_response_schema()
        self.assertFalse(schema["additionalProperties"])
        self.assertIn("human_review_reasons", schema["required"])
        self.assertEqual(
            schema["properties"]["human_review_reasons"]["items"]["enum"],
            [
                "high_or_critical_water_stress",
                "non_water_factor_to_rule_out",
                "ambiguous_visual_evidence",
            ],
        )
        self.assertFalse(
            schema["properties"]["possible_causes"]["items"]["additionalProperties"]
        )
        self.assertIn(
            "pest_to_rule_out",
            schema["properties"]["possible_causes"]["items"]["properties"]
            ["category"]["enum"],
        )


class HumanReviewDecisionTests(unittest.TestCase):
    def test_allows_no_review_when_no_trigger_applies(self) -> None:
        validate_human_review_decision(response())

    def test_low_confidence_does_not_trigger_review(self) -> None:
        validate_human_review_decision(
            response(confidence=0.25, crop_confidence=0.25)
        )

    def test_image_gates_do_not_trigger_review(self) -> None:
        for gate_overrides in (
            {
                "image_quality": {
                    "usable": False,
                    "issues": ["blur"],
                    "retake_guidance": ["Retake a sharp close image."],
                },
            },
            {"crop_is_lettuce": False},
        ):
            with self.subTest(gate_overrides=gate_overrides):
                gated = response(
                    **gate_overrides,
                    stress_level="none",
                    severity_score=0,
                    plant_stress_detected=False,
                    observed_symptoms=[],
                    possible_causes=[],
                    detected_issues=[],
                    needs_human_review=False,
                    human_review_reasons=[],
                )
                validate_water_stress_contract(gated)
                validate_human_review_decision(gated)

    def test_non_water_factor_requires_review(self) -> None:
        non_water_cause = [{
            "category": "pest_to_rule_out",
            "likelihood": "possible",
            "reason": "Visible holes support checking for pests.",
        }]
        validate_human_review_decision(
            response(
                possible_causes=non_water_cause,
                needs_human_review=True,
                human_review_reasons=["non_water_factor_to_rule_out"],
            )
        )

    def test_rejects_generic_review_without_allowed_trigger(self) -> None:
        with self.assertRaisesRegex(ValueError, "without its trigger"):
            validate_human_review_decision(
                response(
                    needs_human_review=True,
                    human_review_reasons=["high_or_critical_water_stress"],
                )
            )

    def test_rejects_extra_reason_when_another_trigger_exists(self) -> None:
        with self.assertRaisesRegex(ValueError, "without its trigger"):
            validate_human_review_decision(
                response(
                    severity_score=4,
                    stress_level="high",
                    needs_human_review=True,
                    human_review_reasons=[
                        "high_or_critical_water_stress",
                        "non_water_factor_to_rule_out",
                    ],
                )
            )

    def test_high_or_critical_severity_requires_review(self) -> None:
        with self.assertRaisesRegex(ValueError, "missing"):
            validate_human_review_decision(
                response(severity_score=4, stress_level="high")
            )
        validate_human_review_decision(
            response(
                severity_score=5,
                stress_level="critical",
                needs_human_review=True,
                human_review_reasons=["high_or_critical_water_stress"],
            )
        )

    def test_allows_ambiguous_visual_evidence_as_the_only_judgment_trigger(self) -> None:
        validate_human_review_decision(
            response(
                needs_human_review=True,
                human_review_reasons=["ambiguous_visual_evidence"],
            )
        )

    def test_new_gemini_contract_accepts_the_normal_case(self) -> None:
        validate_water_stress_contract(response())


class ProviderCompatibilityTests(unittest.IsolatedAsyncioTestCase):
    async def test_mock_provider_includes_review_reasons_in_both_languages(self) -> None:
        for language in ("en", "zh"):
            with self.subTest(language=language):
                result = await MockProvider().analyze(
                    AnalyzeScanRequest(language=language)
                )
                self.assertFalse(result.needs_human_review)
                self.assertEqual(result.human_review_reasons, [])

    def test_generic_api_prompt_keeps_new_field_in_shared_contract(self) -> None:
        prompt = build_api_provider_prompt(AnalyzeScanRequest(language="en"))
        self.assertIn('"human_review_reasons": []', prompt)


if __name__ == "__main__":
    unittest.main()

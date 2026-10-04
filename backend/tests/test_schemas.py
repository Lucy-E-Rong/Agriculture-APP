import unittest

from pydantic import ValidationError

from app.ai.gemini_provider import validate_water_stress_contract
from app.schemas import AnalyzeScanRequest, AnalyzeScanResponse


def valid_result(**overrides) -> dict:
    payload = {
        "crop_is_lettuce": True,
        "crop_confidence": 0.96,
        "image_quality": {"usable": True, "issues": [], "retake_guidance": []},
        "plant_stress_detected": True,
        "stress_level": "low",
        "severity_score": 2,
        "confidence": 0.86,
        "diagnosis": "Visible mild wilting is consistent with water stress.",
        "observed_symptoms": [
            {
                "type": "wilting",
                "location": "outer_leaves",
                "description": "Outer leaves show visible loss of turgor.",
            }
        ],
        "possible_causes": [
            {
                "category": "irrigation_delivery_to_check",
                "likelihood": "possible",
                "reason": "Visible wilting supports checking water delivery.",
            }
        ],
        "detected_issues": ["wilting"],
        "recommendations": ["Check irrigation delivery in this row."],
        "needs_human_review": False,
        "human_review_reasons": [],
    }
    payload.update(overrides)
    return payload


class AnalyzeScanResponseTests(unittest.TestCase):
    def test_fixed_severity_mapping_accepts_every_score(self) -> None:
        expected = {
            0: "none",
            1: "low",
            2: "low",
            3: "medium",
            4: "high",
            5: "critical",
        }
        for score, level in expected.items():
            with self.subTest(score=score):
                if score == 0:
                    payload = valid_result(
                        severity_score=0,
                        stress_level=level,
                        plant_stress_detected=False,
                        observed_symptoms=[],
                        possible_causes=[],
                        detected_issues=[],
                    )
                else:
                    payload = valid_result(severity_score=score, stress_level=level)
                result = AnalyzeScanResponse.model_validate(payload)
                validate_water_stress_contract(result)
                self.assertEqual(result.stress_level, level)

    def test_rejects_mismatched_level_and_score(self) -> None:
        result = AnalyzeScanResponse.model_validate(
            valid_result(severity_score=1, stress_level="medium")
        )
        with self.assertRaisesRegex(ValueError, "stress_level does not match"):
            validate_water_stress_contract(result)

    def test_rejects_positive_water_stress_without_visible_symptoms(self) -> None:
        result = AnalyzeScanResponse.model_validate(valid_result(observed_symptoms=[]))
        with self.assertRaisesRegex(ValueError, "observable symptoms"):
            validate_water_stress_contract(result)

    def test_zero_water_stress_can_retain_non_water_visible_abnormality(self) -> None:
        result = AnalyzeScanResponse.model_validate(
            valid_result(
                severity_score=0,
                stress_level="none",
                plant_stress_detected=False,
                diagnosis="Visible holes require a pest check; no water-stress pattern is visible.",
                observed_symptoms=[{
                    "type": "holes",
                    "location": "leaf_surface",
                    "description": "Several holes are visible on the leaf surface.",
                }],
                possible_causes=[{
                    "category": "pest_to_rule_out",
                    "likelihood": "possible",
                    "reason": "Visible holes support checking for pests.",
                }],
                detected_issues=["leaf_holes"],
                needs_human_review=True,
                human_review_reasons=["non_water_factor_to_rule_out"],
            )
        )
        validate_water_stress_contract(result)
        self.assertEqual(result.severity_score, 0)
        self.assertTrue(result.observed_symptoms)

    def test_unusable_image_cannot_assert_plant_evidence(self) -> None:
        result = AnalyzeScanResponse.model_validate(
            valid_result(
                image_quality={
                    "usable": False,
                    "issues": ["blur"],
                    "retake_guidance": ["Retake a sharp close image."],
                },
                severity_score=0,
                stress_level="none",
                plant_stress_detected=False,
            )
        )
        with self.assertRaisesRegex(ValueError, "cannot assert plant stress"):
            validate_water_stress_contract(result)

    def test_false_human_review_requires_empty_reasons(self) -> None:
        with self.assertRaisesRegex(ValidationError, "must be empty"):
            AnalyzeScanResponse.model_validate(
                valid_result(human_review_reasons=["ambiguous_visual_evidence"])
            )

    def test_gemini_contract_rejects_unapproved_possible_cause_category(self) -> None:
        invalid_cause = [{
            "category": "confirmed_disease",
            "likelihood": "likely",
            "reason": "Unsupported diagnosis.",
        }]
        result = AnalyzeScanResponse.model_validate(
            valid_result(possible_causes=invalid_cause)
        )
        with self.assertRaisesRegex(ValueError, "outside"):
            validate_water_stress_contract(result)

    def test_legacy_persisted_result_remains_readable(self) -> None:
        legacy = valid_result(
            possible_causes=[{
                "category": "water_or_nutrient_stress",
                "likelihood": "possible",
                "reason": "Legacy 0.2 result.",
            }],
            needs_human_review=True,
        )
        legacy.pop("human_review_reasons")
        result = AnalyzeScanResponse.model_validate(legacy)
        self.assertEqual(result.human_review_reasons, [])
        self.assertEqual(result.possible_causes[0].category, "water_or_nutrient_stress")


class AnalyzeScanRequestTests(unittest.TestCase):
    def test_model_selection_defaults_to_gemini_and_accepts_camel_case(self) -> None:
        self.assertEqual(AnalyzeScanRequest().model_id, "gemini-3.6-flash")
        self.assertEqual(AnalyzeScanRequest.model_validate({"modelId": "gpt-5.6-terra"}).model_id, "gpt-5.6-terra")
    def test_scan_context_trims_and_omits_blank_optional_values(self) -> None:
        request = AnalyzeScanRequest.model_validate({
            "locationSnapshot": {
                "display": "  Greenhouse A · Section 2  ",
                "greenhouse": " Greenhouse A ",
                "plant_id": " plant-17 ",
                "period": " Day 3, observation 2 ",
                "sample_id": "",
            }
        })

        self.assertEqual(
            request.location_snapshot.model_dump(exclude_none=True),
            {
                "display": "Greenhouse A · Section 2",
                "greenhouse": "Greenhouse A",
                "plant_id": "plant-17",
                "period": "Day 3, observation 2",
            },
        )

    def test_legacy_growth_stage_remains_readable(self) -> None:
        request = AnalyzeScanRequest.model_validate({
            "locationSnapshot": {"growth_stage": "  early heading  "}
        })

        self.assertEqual(
            request.location_snapshot.model_dump(exclude_none=True),
            {"growth_stage": "early heading"},
        )

    def test_scan_context_rejects_unknown_keys_non_strings_and_long_values(self) -> None:
        invalid_snapshots = [
            {"sensor_temperature": "24 C"},
            {"greenhouse": 7},
            {"row": "x" * 121},
        ]
        for snapshot in invalid_snapshots:
            with self.subTest(snapshot=snapshot):
                with self.assertRaises(ValidationError):
                    AnalyzeScanRequest.model_validate({"locationSnapshot": snapshot})


if __name__ == "__main__":
    unittest.main()

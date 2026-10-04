import json
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from app.ai.gemini_provider import GeminiProvider
from app.ai.prototype_provider import (
    PROTOTYPE_PROMPT,
    PROTOTYPE_TASK,
    PrototypeProvider,
    build_prototype_prompt,
    prototype_response_schema,
)
from app.ai.router import get_ai_provider
from app.config import Settings
from app.schemas import AnalyzeScanRequest


def prototype_shape(**overrides) -> dict:
    payload = {
        "crop_is_lettuce": True,
        "crop_confidence": 0.5,
        "image_quality": {"usable": True, "issues": [], "retake_guidance": []},
        "plant_stress_detected": False,
        "stress_level": "none",
        "severity_score": 5,
        "confidence": 0.5,
        "diagnosis": "The image appears stressed.",
        "observed_symptoms": [],
        "possible_causes": [],
        "detected_issues": [],
        "recommendations": ["Check the plant."],
        "needs_human_review": False,
        "human_review_reasons": [],
    }
    payload.update(overrides)
    return payload


class PrototypeProviderTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.settings = Settings(
            _env_file=None,
            gemini_api_key="synthetic-test-key",
            gemini_model="gemini-test-model",
        )

    def test_prompt_uses_only_the_approved_general_task_and_neutral_formatting(self) -> None:
        prompt = build_prototype_prompt(AnalyzeScanRequest(provider="prototype"))
        self.assertEqual(PROTOTYPE_TASK, (
            "Does it show signs of water stress? Tell me what you notice, how "
            "severe it looks, and what I should check or do next."
        ))
        self.assertTrue(prompt.startswith(PROTOTYPE_TASK))
        self.assertEqual(prompt, PROTOTYPE_PROMPT)
        for forbidden in (
            "Wilting", "Drooping", "Loss of turgor", "Leaf curling",
            "No obvious abnormality", "red, purple", "1-2 low",
            "water_availability_to_check", "disease_to_rule_out",
            "high_or_critical_water_stress", "ambiguous_visual_evidence",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, prompt)

    def test_schema_uses_the_existing_online_response_shape(self) -> None:
        schema = prototype_response_schema()
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(
            set(schema["required"]),
            {
                "crop_is_lettuce", "crop_confidence", "image_quality",
                "plant_stress_detected", "stress_level", "severity_score",
                "confidence", "diagnosis", "observed_symptoms",
                "possible_causes", "detected_issues", "recommendations",
                "needs_human_review", "human_review_reasons",
            },
        )

    async def test_uses_same_model_temperature_and_image_bytes_as_farmscout_path(self) -> None:
        provider = PrototypeProvider(self.settings)
        response = MagicMock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "candidates": [{"content": {"parts": [{
                "text": json.dumps(prototype_shape()),
            }]}}]
        }
        client_instance = MagicMock()
        client_instance.post = AsyncMock(return_value=response)
        async_client = MagicMock()
        async_client.__aenter__ = AsyncMock(return_value=client_instance)
        async_client.__aexit__ = AsyncMock(return_value=None)
        image_bytes = "/9j/2Q=="

        with patch("app.ai.prototype_provider.httpx.AsyncClient", return_value=async_client):
            result = await provider.analyze(AnalyzeScanRequest(
                provider="prototype", image_base64=image_bytes,
                image_mime_type="image/jpeg",
            ))

        self.assertEqual(result.severity_score, 5)
        call = client_instance.post.await_args
        self.assertIn("gemini-test-model:generateContent", call.args[0])
        payload = call.kwargs["json"]
        self.assertEqual(payload["generationConfig"]["temperature"], 0.15)
        self.assertEqual(
            payload["contents"][0]["parts"][1]["inlineData"]["data"],
            image_bytes,
        )

    async def test_does_not_apply_farmscout_semantic_validators(self) -> None:
        provider = PrototypeProvider(self.settings)
        response = MagicMock()
        response.raise_for_status.return_value = None
        # This is valid AnalyzeScanResponse shape but deliberately violates the
        # FarmScout severity/level and visible-evidence rules.
        response.json.return_value = {
            "candidates": [{"content": {"parts": [{
                "text": json.dumps(prototype_shape()),
            }]}}]
        }
        client_instance = MagicMock()
        client_instance.post = AsyncMock(return_value=response)
        async_client = MagicMock()
        async_client.__aenter__ = AsyncMock(return_value=client_instance)
        async_client.__aexit__ = AsyncMock(return_value=None)

        with patch("app.ai.prototype_provider.httpx.AsyncClient", return_value=async_client):
            result = await provider.analyze(AnalyzeScanRequest(
                provider="prototype", image_base64="/9j/2Q==",
            ))

        self.assertEqual(result.stress_level, "none")
        self.assertEqual(result.severity_score, 5)
        self.assertFalse(result.plant_stress_detected)

    def test_provider_router_keeps_visual_ab_mapping(self) -> None:
        self.assertIsInstance(get_ai_provider("gemini", self.settings), GeminiProvider)
        self.assertIsInstance(get_ai_provider("prototype", self.settings), PrototypeProvider)


if __name__ == "__main__":
    unittest.main()

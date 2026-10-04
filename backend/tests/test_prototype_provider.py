import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from app.ai.gemini_provider import GeminiProvider
from app.ai.prototype_provider import (
    PROTOTYPE_PROMPT,
    PROTOTYPE_TASK,
    PrototypeProvider,
    build_prototype_prompt,
)
from app.ai.router import get_ai_provider
from app.ai.openai_responses_provider import OpenAIResponsesProvider
from app.config import Settings
from app.schemas import AnalyzeScanRequest


class PrototypeProviderTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.settings = Settings(
            _env_file=None,
            gemini_api_key="synthetic-test-key",
            gemini_model="gemini-test-model",
        )

    def test_prompt_uses_only_the_approved_general_task(self) -> None:
        prompt = build_prototype_prompt(AnalyzeScanRequest(provider="prototype"))
        self.assertEqual(PROTOTYPE_TASK, (
            "Does it show signs of water stress? Tell me what you notice, how "
            "severe it looks, and what I should check or do next."
        ))
        self.assertEqual(prompt, PROTOTYPE_PROMPT)
        for forbidden in (
            "Wilting", "Drooping", "Loss of turgor", "Leaf curling",
            "No obvious abnormality", "red, purple", "1-2 low",
            "water_availability_to_check", "disease_to_rule_out",
            "high_or_critical_water_stress", "ambiguous_visual_evidence",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, prompt)

    async def test_uses_same_model_temperature_and_image_bytes_as_farmscout_path(self) -> None:
        provider = PrototypeProvider(self.settings)
        response = MagicMock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "candidates": [{"content": {"parts": [{
                "text": "The leaves look slightly droopy. Check irrigation and soil moisture.",
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

        self.assertEqual(result.response_kind, "prototype")
        self.assertIn("slightly droopy", result.response_text)
        call = client_instance.post.await_args
        self.assertIn("gemini-test-model:generateContent", call.args[0])
        payload = call.kwargs["json"]
        self.assertEqual(payload["generationConfig"]["temperature"], 0.15)
        self.assertNotIn("responseMimeType", payload["generationConfig"])
        self.assertNotIn("responseJsonSchema", payload["generationConfig"])
        self.assertEqual(
            payload["contents"][0]["parts"][1]["inlineData"]["data"],
            image_bytes,
        )

    async def test_returns_non_json_text_without_farmscout_validation(self) -> None:
        provider = PrototypeProvider(self.settings)
        response = MagicMock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "candidates": [{"content": {"parts": [{
                "text": "I notice some curling and loss of vigor. It looks moderately stressed.",
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

        self.assertEqual(result.response_kind, "prototype")
        self.assertTrue(result.response_text.startswith("I notice"))

    def test_provider_router_keeps_visual_ab_mapping(self) -> None:
        self.assertIsInstance(get_ai_provider("gemini", "gemini-3.6-flash", self.settings), GeminiProvider)
        self.assertIsInstance(get_ai_provider("prototype", "gemini-3.6-flash", self.settings), PrototypeProvider)
        self.assertIsInstance(get_ai_provider("gemini", "gpt-5.6-terra", self.settings), OpenAIResponsesProvider)


if __name__ == "__main__":
    unittest.main()

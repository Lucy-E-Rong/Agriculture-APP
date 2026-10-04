import json
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from app.ai.openai_responses_provider import OpenAIResponsesProvider
from app.config import Settings
from app.schemas import AnalyzeScanRequest


def response_text(text: str):
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"output": [{"type": "message", "content": [{"type": "output_text", "text": text}]}]}
    return response


class OpenAIResponsesProviderTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.settings = Settings(_env_file=None, openai_api_key="synthetic", openai_model="gpt-5.6-terra")

    async def test_prototype_uses_responses_free_text_without_json_schema(self):
        client = MagicMock(); client.post = AsyncMock(return_value=response_text("Visible leaves look droopy."))
        context = MagicMock(); context.__aenter__ = AsyncMock(return_value=client); context.__aexit__ = AsyncMock(return_value=None)
        with patch("app.ai.openai_responses_provider.httpx.AsyncClient", return_value=context):
            result = await OpenAIResponsesProvider(self.settings, "prototype").analyze(AnalyzeScanRequest(provider="prototype", model_id="gpt-5.6-terra", image_base64="/9j/2Q=="))
        self.assertEqual(result.response_kind, "prototype")
        payload = client.post.await_args.kwargs["json"]
        self.assertEqual(client.post.await_args.args[0], "https://api.openai.com/v1/responses")
        self.assertNotIn("text", payload)
        self.assertFalse(payload["store"])

    async def test_farmscout_uses_existing_structured_semantics(self):
        structured = {"crop_is_lettuce": True, "crop_confidence": .9, "image_quality": {"usable": True, "issues": [], "retake_guidance": []}, "plant_stress_detected": False, "stress_level": "none", "severity_score": 0, "confidence": .9, "diagnosis": "Healthy", "observed_symptoms": [], "possible_causes": [], "detected_issues": [], "recommendations": [], "needs_human_review": False, "human_review_reasons": []}
        client = MagicMock(); client.post = AsyncMock(return_value=response_text(json.dumps(structured)))
        context = MagicMock(); context.__aenter__ = AsyncMock(return_value=client); context.__aexit__ = AsyncMock(return_value=None)
        with patch("app.ai.openai_responses_provider.httpx.AsyncClient", return_value=context):
            result = await OpenAIResponsesProvider(self.settings, "gemini").analyze(AnalyzeScanRequest(model_id="gpt-5.6-terra", image_base64="/9j/2Q=="))
        self.assertEqual(result.response_kind, "farmscout")
        payload = client.post.await_args.kwargs["json"]
        self.assertEqual(payload["text"]["format"]["type"], "json_schema")
        self.assertEqual(payload["model"], "gpt-5.6-terra")

    async def test_rejects_non_terra_openai_configuration(self):
        settings = Settings(_env_file=None, openai_api_key="synthetic", openai_model="other")
        with self.assertRaisesRegex(RuntimeError, "OPENAI_MODEL"):
            await OpenAIResponsesProvider(settings, "prototype").analyze(AnalyzeScanRequest(model_id="gpt-5.6-terra", image_base64="/9j/2Q=="))

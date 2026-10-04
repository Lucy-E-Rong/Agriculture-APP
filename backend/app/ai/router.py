from app.ai.api_provider import ApiProvider
from app.ai.base import AiProviderClient
from app.ai.local_vlm import LocalVlmProvider
from app.ai.gemini_provider import GeminiProvider
from app.ai.mock_provider import MockProvider
from app.ai.prototype_provider import PrototypeProvider
from app.ai.openai_responses_provider import OpenAIResponsesProvider
from app.config import Settings
from app.schemas import AiProvider


def get_ai_provider(provider: AiProvider, model_id: str, settings: Settings) -> AiProviderClient:
    if model_id == "gpt-5.6-terra" and provider in {"gemini", "prototype"}:
        return OpenAIResponsesProvider(settings, provider)
    if provider == "gemini":
        return GeminiProvider(settings)
    if provider == "prototype":
        return PrototypeProvider(settings)
    if provider == "local_vlm":
        return LocalVlmProvider(settings)
    if provider == "mock":
        return MockProvider()
    return ApiProvider(settings)

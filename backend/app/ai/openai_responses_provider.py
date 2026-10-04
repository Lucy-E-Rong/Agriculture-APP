"""OpenAI Responses adapter for the existing FarmScout and Prototype semantics."""

from __future__ import annotations

import json

import httpx

from app.ai.base import AiProviderClient
from app.ai.gemini_provider import (
    build_prompt as build_farmscout_prompt,
    gemini_response_schema,
    validate_human_review_decision,
    validate_water_stress_contract,
)
from app.ai.prototype_provider import build_prototype_prompt
from app.config import Settings
from app.schemas import AnalyzeScanRequest, AnalyzeScanResponse, AnalysisResponse, PrototypeAnalysisResponse


class OpenAIResponsesProvider(AiProviderClient):
    def __init__(self, settings: Settings, semantic_provider: str):
        self.settings = settings
        self.semantic_provider = semantic_provider

    async def analyze(self, request: AnalyzeScanRequest) -> AnalysisResponse:
        if not self.settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured")
        if self.settings.openai_model != "gpt-5.6-terra":
            raise RuntimeError("OPENAI_MODEL must be gpt-5.6-terra for this selection")
        if not request.image_base64:
            raise ValueError("OpenAI analysis requires imageBase64")
        structured = self.semantic_provider == "gemini"
        prompt = build_farmscout_prompt(request) if structured else build_prototype_prompt(request)
        payload: dict[str, object] = {
            "model": self.settings.openai_model,
            "store": False,
            "input": [{"role": "user", "content": [
                {"type": "input_text", "text": prompt},
                {"type": "input_image", "image_url": f"data:{request.image_mime_type};base64,{request.image_base64}", "detail": "high"},
            ]}],
        }
        if structured:
            payload["text"] = {"format": {"type": "json_schema", "name": "farmscout_assessment", "strict": True, "schema": gemini_response_schema()}}
        async with httpx.AsyncClient(timeout=90) as client:
            response = await client.post("https://api.openai.com/v1/responses", json=payload, headers={"Authorization": f"Bearer {self.settings.openai_api_key}"})
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise RuntimeError("OpenAI Responses API rejected the request") from exc
            data = response.json()
        try:
            text = next(part["text"] for item in data["output"] if item.get("type") == "message" for part in item.get("content", []) if part.get("type") == "output_text")
        except (KeyError, IndexError, StopIteration, TypeError) as exc:
            raise RuntimeError("OpenAI Responses returned no analysis") from exc
        if not isinstance(text, str) or not text.strip():
            raise RuntimeError("OpenAI Responses returned an empty analysis")
        if not structured:
            return PrototypeAnalysisResponse(response_text=text.strip())
        try:
            result = AnalyzeScanResponse.model_validate(json.loads(text))
            validate_water_stress_contract(result)
            validate_human_review_decision(result)
            return result
        except (json.JSONDecodeError, ValueError) as exc:
            raise RuntimeError("OpenAI Responses returned an invalid structured response") from exc

from abc import ABC, abstractmethod
from app.schemas import AnalysisResponse, AnalyzeScanRequest


class AiProviderClient(ABC):
    @abstractmethod
    async def analyze(self, request: AnalyzeScanRequest) -> AnalysisResponse:
        raise NotImplementedError

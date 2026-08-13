from abc import ABC, abstractmethod
from app.schemas import AnalyzeScanRequest, AnalyzeScanResponse


class AiProviderClient(ABC):
    @abstractmethod
    async def analyze(self, request: AnalyzeScanRequest) -> AnalyzeScanResponse:
        raise NotImplementedError


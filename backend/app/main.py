import secrets

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.ai.router import get_ai_provider
from app.config import get_settings
from app.schemas import AnalyzeScanRequest, AnalyzeScanResponse, HealthResponse

settings = get_settings()

app = FastAPI(title="FarmScout API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        app_env=settings.app_env,
        gemini_configured=bool(settings.gemini_api_key),
        gemini_model=settings.gemini_model,
    )


def verify_demo_access_code(x_demo_access_code: str | None) -> None:
    expected = settings.demo_access_code
    if expected and (not x_demo_access_code or not secrets.compare_digest(x_demo_access_code, expected)):
        raise HTTPException(status_code=401, detail="Invalid demo access code")


@app.get("/access/verify")
async def verify_access(x_demo_access_code: str | None = Header(default=None)) -> dict[str, bool]:
    verify_demo_access_code(x_demo_access_code)
    return {"ok": True}


@app.post("/api/scans/analyze", response_model=AnalyzeScanResponse)
async def analyze_scan(
    request: AnalyzeScanRequest,
    x_demo_access_code: str | None = Header(default=None),
) -> AnalyzeScanResponse:
    verify_demo_access_code(x_demo_access_code)
    provider = get_ai_provider(request.provider, settings)
    try:
        return await provider.analyze(request)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI analysis failed: {exc}") from exc

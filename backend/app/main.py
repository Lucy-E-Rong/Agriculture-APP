import secrets
from uuid import UUID, uuid4

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from app.audit import (
    AUDITED_ROUTES,
    CloudAuditWriter,
    build_audit_event,
    configure_provider_audit,
    emit_audit_safely,
    provider_error_category,
)
from app.ai.router import get_ai_provider
from app.config import get_settings

from app.schemas import (
    AnalyzeScanRequest,
    HealthResponse,
    PersistedAnalyzeScanResponse,
    RecentScan,
    ScanDetail,
)
from app.supabase_persistence import PersistenceError, ScanNotFoundError, SupabaseScanStore

settings = get_settings()

app = FastAPI(title="FarmScout API", version="0.3.0")
app.state.audit_writer = CloudAuditWriter(settings)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def audit_relevant_requests(request: Request, call_next):
    action = AUDITED_ROUTES.get((request.method, request.url.path))
    if action is None:
        return await call_next(request)

    request_id = str(uuid4())
    request.state.audit_external_api_used = False
    request.state.audit_provider = None
    request.state.audit_provider_outcome = "not_called"
    try:
        response = await call_next(request)
    except Exception:
        event = build_audit_event(request, settings, action, 500, request_id)
        await emit_audit_safely(
            request.app.state.audit_writer,
            event,
            request.headers.get("x-vercel-oidc-token"),
        )
        raise

    event = build_audit_event(request, settings, action, response.status_code, request_id)
    await emit_audit_safely(
        request.app.state.audit_writer,
        event,
        request.headers.get("x-vercel-oidc-token"),
    )
    return response


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


def model_name_for_provider(provider: str) -> str | None:
    if provider == "gemini":
        return settings.gemini_model
    if provider == "prototype":
        return settings.gemini_model
    if provider == "local_vlm":
        return settings.local_vlm_url
    if provider == "api_provider":
        if settings.openai_api_key:
            return settings.openai_model
        if settings.anthropic_api_key:
            return settings.anthropic_model
        return "mock"
    return "mock"


@app.post("/api/scans/analyze", response_model=PersistedAnalyzeScanResponse)
async def analyze_scan(
    request: AnalyzeScanRequest,
    http_request: Request,
    x_demo_access_code: str | None = Header(default=None),
) -> PersistedAnalyzeScanResponse:
    verify_demo_access_code(x_demo_access_code)
    configure_provider_audit(http_request, request.provider, settings)
    provider = get_ai_provider(request.provider, settings)
    try:
        analysis = await provider.analyze(request)
    except Exception as exc:
        http_request.state.audit_provider_outcome = "failed"
        http_request.state.audit_error_category = provider_error_category(exc)
        raise HTTPException(status_code=502, detail=f"AI analysis failed: {exc}") from exc
    if http_request.state.audit_external_api_used:
        http_request.state.audit_provider_outcome = "succeeded"
    try:
        store = SupabaseScanStore(settings)
        return await store.persist_success(request, analysis, model_name_for_provider(request.provider))
    except PersistenceError as exc:
        http_request.state.audit_error_category = "persistence_failed"
        raise HTTPException(status_code=503, detail="Analysis succeeded but could not be saved") from exc


@app.get("/api/scans/recent", response_model=list[RecentScan])
async def recent_scans(
    x_demo_access_code: str | None = Header(default=None),
) -> list[RecentScan]:
    verify_demo_access_code(x_demo_access_code)
    try:
        return await SupabaseScanStore(settings).list_recent(limit=10)
    except PersistenceError as exc:
        raise HTTPException(status_code=503, detail="Recent scans are temporarily unavailable") from exc


@app.get("/api/scans/{scan_id}", response_model=ScanDetail)
async def scan_detail(
    scan_id: UUID,
    x_demo_access_code: str | None = Header(default=None),
) -> ScanDetail:
    verify_demo_access_code(x_demo_access_code)
    try:
        return await SupabaseScanStore(settings).get_detail(scan_id)
    except ScanNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Scan not found") from exc
    except PersistenceError as exc:
        raise HTTPException(status_code=503, detail="Scan detail is temporarily unavailable") from exc

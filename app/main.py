from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.database import close_db
from app.routers import contratacoes, etl, auth, lgpd

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_db()

app = FastAPI(
    title="Projeto Integrador — PNCP API",
    description="API para consulta e ingestão de dados de contratações do PNCP (Portal Nacional de Contratações Públicas).",
    version="1.0.0",
    lifespan=lifespan,
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = [
        {"campo": " -> ".join(str(loc) for loc in err["loc"]), "erro": err["msg"]}
        for err in exc.errors()
    ]
    return JSONResponse(status_code=400, content={"detail": errors})

app.include_router(auth.router)
app.include_router(lgpd.router)
app.include_router(contratacoes.router)
app.include_router(etl.router)

@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}
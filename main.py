import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.db.connection import close_db_pool, get_db_pool

# Importa cada 'router' diretamente do seu arquivo e dá um apelido (alias)
from src.api.routes.profile import router as profile_router
from src.api.routes.spots import router as spots_router
from src.api.routes.preferences import router as preferences_router
from src.api.routes.presets import router as presets_router
from src.api.routes.recommendations import router as recommendations_router
from src.api.routes.forecasts import router as forecasts_router

app = FastAPI(
    title="The Check API",
    version="2.0.0",
    description="API para recomendações de surf personalizadas."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    await get_db_pool()
    print("API iniciada e pool de conexões pronto.")

@app.on_event("shutdown")
async def shutdown_event():
    await close_db_pool()
    print("API encerrada e pool de conexões fechado.")


# Inclusão dos roteadores da API usando os apelidos
app.include_router(profile_router)
app.include_router(spots_router)
app.include_router(preferences_router)
app.include_router(presets_router)
app.include_router(recommendations_router)
app.include_router(forecasts_router)


@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Bem-vindo à API V2 do The Check!"}
    
@app.get("/health", tags=["Health Check"])
async def health_check():
    """
    Endpoint simples para monitoramento de saúde da API.
    """
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
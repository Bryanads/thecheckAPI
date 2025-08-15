# src/api/__init__.py
def create_app():
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from src.db.connection import init_async_db_pool

    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Importa e inclui os routers
    from .routes.recommendation_routes import router as recommendation_router
    from .routes.forecast_routes import router as forecast_router
    from .routes.spot_routes import router as spot_router
    from .routes.user_routes import router as user_router
    from .routes.preset_routes import router as preset_router
    from .routes.level_spot_preferences_routes import router as level_spot_preferences_router # NOVO
    from .routes.user_spot_preferences_routes import router as user_spot_preferences_router # NOVO

    app.include_router(recommendation_router)
    app.include_router(forecast_router)
    app.include_router(spot_router)
    app.include_router(user_router)
    app.include_router(preset_router)
    app.include_router(level_spot_preferences_router) # NOVO
    app.include_router(user_spot_preferences_router) # NOVO

    @app.on_event("startup")
    async def startup_event():
        await init_async_db_pool()

    return app
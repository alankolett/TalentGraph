from fastapi import FastAPI

from common.settings import Settings, get_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(title=settings.app_name)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {
            "status": "ok",
            "app": settings.app_name,
            "environment": settings.environment,
            "llm_provider": settings.llm_provider,
            "qdrant_url": settings.qdrant_url,
        }

    return app


app = create_app()

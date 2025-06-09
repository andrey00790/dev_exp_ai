from fastapi import FastAPI

from app.api import health


def create_app() -> FastAPI:
    application = FastAPI()
    application.include_router(health.router)
    return application


app = create_app()


if __name__ == '__main__':
    import uvicorn
    uvicorn.run('app.main:app', host='0.0.0.0', port=8000)

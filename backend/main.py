import uvicorn

from config import config
from core.app_factory import create_app


app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.host,
        port=config.port,
        reload=True,
        log_level="info",
    )

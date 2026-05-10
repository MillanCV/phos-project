import os
from src.interfaces.http.app import create_app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=os.getenv("PHOS_HOST", "0.0.0.0"),
        port=int(os.getenv("PHOS_PORT", "8000")),
    )

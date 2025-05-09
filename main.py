# main.py (at project root)

import uvicorn

if __name__ == "__main__":
    # Note: "app.main:app" points to the FastAPI instance in app/main.py
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,            # auto-reload on code changes
        log_level="info"
    )

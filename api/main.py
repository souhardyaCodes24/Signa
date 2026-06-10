"""
main.py — FastAPI application entry point for Signa.

Start the dev server:
    python -m api.main

Then:
  - Open http://127.0.0.1:8000 in your browser (web UI)
  - Use python -m cli.main scan <file>  (CLI)
"""

from fastapi import FastAPI

from api.routes import router   # the /api/lookup endpoint
from ui.routes import router as ui_router  # the web UI pages
from db.schema import Base
from api.database import engine

# Create tables on startup
Base.metadata.create_all(bind=engine)

# FastAPI app instance
app = FastAPI(
    title="Signa API",
    description="Privacy-preserving threat intelligence API",
    version="0.1.0",
)

# Register API routes
app.include_router(router)

# Register Web UI routes (this handles GET / for the HTML page)
app.include_router(ui_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="127.0.0.1", port=8000, reload=True)

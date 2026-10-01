from fastapi import FastAPI
from api.routes import forge, lens

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Narrative Intelligence Engine API",
    description="Unified API for Narrative Forge and Narrative Lens, powered by StoryScope taxonomy.",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(forge.router, prefix="/api/forge", tags=["Forge"])
app.include_router(lens.router, prefix="/api/lens", tags=["Lens"])
# app.include_router(analysis.router, prefix="/api/analysis", tags=["Analysis"])
# app.include_router(reports.router, prefix="/api/report", tags=["Reports"])

@app.get("/health")
def health_check():
    return {"status": "ok", "engine": "NIE-0.1.0"}

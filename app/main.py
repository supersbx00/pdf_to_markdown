from fastapi import FastAPI

from app.src.api.documentos.documentos_router import router as documentos_router

app = FastAPI(title="documentos_md_uaysen")
app.include_router(documentos_router)


@app.get("/")
def root():
    return {"status": "ok"}

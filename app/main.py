from fastapi import FastAPI
from fastapi_mcp import FastApiMCP

from app.src.api.documentos.documentos_router import router as documentos_router

app = FastAPI(title="documentos_md_uaysen")
app.include_router(documentos_router)

mcp = FastApiMCP(app, include_operations=["convertir_pdf_a_md"])
mcp.mount_http(mount_path="/mcp")


@app.get("/")
def root():
    return {"status": "ok"}

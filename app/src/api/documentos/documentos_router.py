from fastapi import APIRouter, UploadFile
from pydantic import BaseModel

from app.src.api.documentos import documentos_controller as controller

router = APIRouter(prefix="/documentos", tags=["documentos"])


class ConvertirPdfAMdRequest(BaseModel):
    nombre: str
    contenido_base64: str


@router.post("/convertir")
async def convertir(archivo: UploadFile):
    return await controller.convertir_pdf(archivo)


@router.post("/descargar")
async def descargar(archivo: UploadFile):
    return await controller.descargar_pdf(archivo)


@router.post("/convertir-base64", operation_id="convertir_pdf_a_md")
async def convertir_base64(body: ConvertirPdfAMdRequest):
    return await controller.convertir_pdf_a_md(body)

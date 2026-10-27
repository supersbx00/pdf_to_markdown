from fastapi import APIRouter, UploadFile

from app.src.api.documentos import documentos_controller as controller

router = APIRouter(prefix="/documentos", tags=["documentos"])


@router.post("/convertir")
async def convertir(archivo: UploadFile):
    return await controller.convertir_pdf(archivo)


@router.post("/descargar")
async def descargar(archivo: UploadFile):
    return await controller.descargar_pdf(archivo)

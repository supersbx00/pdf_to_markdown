import base64
import binascii
from urllib.parse import quote

from fastapi import HTTPException, Response, UploadFile

from app.src.api.documentos import documentos_service as service


async def convertir_pdf(archivo: UploadFile) -> dict:
    try:
        contenido = await archivo.read()
        return await service.convertir(archivo.filename, contenido)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def convertir_pdf_a_md(body) -> dict:
    try:
        contenido = base64.b64decode(body.contenido_base64, validate=True)
        return await service.convertir(body.nombre, contenido)
    except HTTPException:
        raise
    except binascii.Error:
        raise HTTPException(status_code=400, detail="El contenido no es base64 válido")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def descargar_pdf(archivo: UploadFile) -> Response:
    try:
        contenido = await archivo.read()
        nombre, datos = await service.descargar(archivo.filename, contenido)
        return Response(
            content=datos,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(nombre)}"},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

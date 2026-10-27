import re

import pymupdf
from fastapi import HTTPException
from fastapi.concurrency import run_in_threadpool

from app.src.api.documentos.documentos_mapper import (
    armar_indice,
    armar_markdown,
    quitar_indice_pdf,
    to_conversion_response,
    to_zip,
)

MAX_BYTES = 20 * 1024 * 1024


def _validar(contenido: bytes) -> None:
    if len(contenido) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="El archivo supera el tamaño máximo de 20 MB")
    if not contenido.startswith(b"%PDF-"):
        raise HTTPException(status_code=400, detail="El archivo no es un PDF válido")


def _abrir(contenido: bytes) -> pymupdf.Document:
    try:
        doc = pymupdf.open(stream=contenido, filetype="pdf")
    except Exception:
        raise HTTPException(status_code=400, detail="El PDF no se pudo leer: el archivo está dañado")
    if doc.needs_pass:
        doc.close()
        raise HTTPException(status_code=400, detail="El PDF está protegido con contraseña")
    return doc


def _validar_texto(markdown: str) -> None:
    if not markdown.strip():
        raise HTTPException(
            status_code=422,
            detail="El PDF no tiene texto extraíble (posiblemente escaneado); no se realiza OCR",
        )


def _pdf_to_markdown(contenido: bytes) -> tuple[int, str]:
    with _abrir(contenido) as doc:
        return doc.page_count, doc.to_markdown(use_ocr=False)


def _lineas(page: pymupdf.Page, bbox: tuple) -> list[str]:
    bloques = page.get_text("dict", clip=pymupdf.Rect(bbox))["blocks"]
    lineas = ("".join(s["text"] for s in l["spans"]).strip() for b in bloques for l in b.get("lines", []))
    return [l for l in lineas if l]


def _pdf_to_chunks(contenido: bytes) -> tuple[list, list[dict], list[tuple[float, float]], list[dict]]:
    with _abrir(contenido) as doc:
        chunks = doc.to_markdown(use_ocr=False, embed_images=True, page_chunks=True)
        lineas = [
            {b["index"]: _lineas(page, b["bbox"]) for b in chunk["page_boxes"] if b["class"] == "text"}
            for page, chunk in zip(doc, chunks)
        ]
        return doc.get_toc(), chunks, [(p.rect.width, p.rect.height) for p in doc], lineas


async def convertir(nombre: str, contenido: bytes) -> dict:
    _validar(contenido)
    paginas, markdown = await run_in_threadpool(_pdf_to_markdown, contenido)
    _validar_texto(markdown)
    return to_conversion_response(nombre, paginas, markdown)


async def descargar(nombre: str, contenido: bytes) -> tuple[str, bytes]:
    _validar(contenido)
    toc, chunks, tamanos, lineas = await run_in_threadpool(_pdf_to_chunks, contenido)
    markdown, imagenes = armar_markdown(chunks, tamanos, lineas)
    _validar_texto(re.sub(r"!\[\]\(imagenes/[^)]+\)", "", markdown))
    markdown, toc = quitar_indice_pdf(markdown, toc)
    return to_zip(nombre, armar_indice(markdown, toc), imagenes)

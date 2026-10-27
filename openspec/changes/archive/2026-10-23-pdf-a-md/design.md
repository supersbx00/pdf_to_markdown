# Design

## Context

- La API vive en `app/main.py` (FastAPI, un solo endpoint `/`). El `Dockerfile` copia solo `app/` y arranca con `fastapi run app/main.py`.
- `architecture.md` exige que cada feature viva en `src/api/<feature>/` con archivos `<feature>_<capa>.py`; en este proyecto `src/` va dentro de `app/` (`app/src/api/<feature>/`). Hoy no existe.
- El devcontainer usa Python 3.11 y el `Dockerfile` usa Python 3.13; ambas versiones tienen wheels de PyMuPDF.
- No hay suite de pruebas previa (línea base vacía).

## Goals / Non-Goals

**Goals:**
- Feature `documentos` con Router → Controller → Service → Mapper.
- Conversión robusta con errores HTTP claros (ver spec).
- Pruebas de integración con `TestClient` que cubren cada escenario del spec.

**Non-Goals:**
- OCR, extracción de imágenes, otros formatos, persistencia.

## Decisions

**Estructura del feature** (`app/src/api/documentos/`):
- `documentos_router.py`: `APIRouter(prefix="/documentos")`, `POST /convertir` con `archivo: UploadFile`; delega al controller.
- `documentos_controller.py`: lee los bytes del `UploadFile`, llama al service y aplica la regla de excepciones (re-lanza `HTTPException`, envuelve el resto en 500).
- `documentos_service.py`: valida tamaño (413) y firma `%PDF-` (400), abre con `pymupdf.open(stream=..., filetype="pdf")` (400 si falla), revisa `doc.needs_pass` (400), convierte con `doc.to_markdown(use_ocr=False)` y responde 422 si el resultado queda vacío tras `strip()`.
- `documentos_mapper.py`: función pura que arma la respuesta `{archivo, paginas, markdown}`.
- Sin `documentos_repository.py`: no hay persistencia (coding_standards §5).
- Se agregan `app/src/__init__.py`, `app/src/api/__init__.py` y `app/src/api/documentos/__init__.py` para que el paquete sea importable.

**Librería: pymupdf 2.x** en vez de markitdown (texto casi plano, sin títulos ni tablas) o docling (torch, del orden de GB). Desde la 2.0, el código de pymupdf4llm vive dentro de `pymupdf` (el paquete `pymupdf4llm` 2.0 está vacío) y trae un modelo de layout ONNX (~250 MB en total). Se descartó fijar `pymupdf4llm==0.3.4` (sin modelo, ~50 MB) por ser una versión antigua sin mantenimiento; el usuario eligió la versión actual. Es gratuita (AGPL), lo que el usuario aceptó.

**OCR desactivado explícitamente** (`use_ocr=False`): el conversor intenta OCR por defecto; el spec exige no hacerlo y responder 422 si no hay texto.

**Conversión en threadpool**: `to_markdown` es CPU-bound y síncrona; el service la ejecuta con `fastapi.concurrency.run_in_threadpool` para no bloquear el event loop.

**Todo en memoria**: el PDF se abre desde bytes (`stream=`), sin archivos temporales, lo que cumple el requisito de no persistencia.

**Respuesta JSON** en vez de `text/markdown` plano: permite incluir `archivo` y `paginas` y es el formato natural de FastAPI/OpenAPI.

**Importación desde `app/main.py`**: `from app.src.api.documentos.documentos_router import router`. `fastapi run app/main.py` agrega la raíz del proyecto a `sys.path` (porque `app/` es paquete), así que `app.src` resuelve. Como `src/` vive dentro de `app/`, el `Dockerfile` (`COPY app ./app`) y el volumen de `docker-compose.yml` ya lo incluyen sin cambios.

**Pruebas**: `tests/test_documentos.py` con `fastapi.testclient.TestClient`. Los PDFs de prueba se generan en memoria con `pymupdf` (texto, título grande, página en blanco, cifrado), así no hay binarios en el repo.

## Risks / Trade-offs

- [AGPL de PyMuPDF] → Aceptado por el usuario. Si la API se expone públicamente, hay que publicar el código.
- [El límite de 20 MB se valida después de leer el archivo en memoria] → Aceptable para el volumen esperado; si fuera necesario, se puede limitar antes en un proxy.
- [PDFs con layout complejo (columnas, tablas sin bordes) pueden quedar imperfectos] → Limitación conocida de la extracción sin ML; fuera de alcance.
- [PDF con poco texto mezclado con imágenes escaneadas] → Se convierte solo el texto disponible; únicamente se rechaza con 422 si no hay ningún texto.

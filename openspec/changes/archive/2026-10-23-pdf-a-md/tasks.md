# Tasks

## 1. Dependencias e infraestructura

- [x] 1.1 Agregar `pymupdf>=2,<3` y `pytest` a `requirements.txt`, instalar con `pip install -r requirements.txt` y verificar con `python -c "import pymupdf; pymupdf.Document.to_markdown"`
- [x] 1.2 Verificar que `Dockerfile` (`COPY app ./app`) y `docker-compose.yml` (volumen `./app`) ya incluyen `app/src/` sin cambios
- [x] 1.3 Crear `app/src/__init__.py`, `app/src/api/__init__.py` y `app/src/api/documentos/__init__.py`; verificar con `python -c "import app.src.api.documentos"`

## 2. Feature documentos

- [x] 2.1 Implementar `app/src/api/documentos/documentos_mapper.py` (función pura que arma `{archivo, paginas, markdown}`)
- [x] 2.2 Implementar `documentos_service.py` con las validaciones 413/400/422 y la conversión en threadpool, según design.md
- [x] 2.3 Implementar `documentos_controller.py` con la regla de excepciones de `architecture.md`
- [x] 2.4 Implementar `documentos_router.py` (`POST /documentos/convertir`) y registrarlo en `app/main.py`; verificar que la ruta aparece en `/openapi.json`
- [x] 2.5 Escribir `tests/test_documentos.py` con un test por escenario del spec (PDF válido, encabezado `#`, .txt, PDF corrupto, PDF cifrado, PDF sin texto, archivo > 20 MB), generando los PDFs en memoria con `pymupdf`; verificar con `pytest` en verde

## 3. Integración

- [x] 3.1 Levantar la API con `fastapi dev app/main.py` y convertir un PDF real con `curl -F archivo=@<pdf> localhost:8000/documentos/convertir`; verificar que responde 200 con Markdown legible

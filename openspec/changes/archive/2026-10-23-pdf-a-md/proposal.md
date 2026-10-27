# Proposal

## Why

Los documentos de la universidad llegan en PDF y se necesitan en Markdown para poder editarlos, versionarlos y procesarlos (por ejemplo, alimentar herramientas de IA o publicarlos). Hoy la API solo tiene un endpoint de salud; no existe forma de convertir un PDF a Markdown.

## What Changes

- Nuevo endpoint `POST /documentos/convertir` que recibe un archivo PDF (multipart/form-data) y responde su contenido en Markdown, conservando títulos, listas y tablas en lo posible.
- Solo PDFs con texto extraíble. Los PDFs escaneados (solo imagen) se rechazan con un error claro; no hay OCR.
- Sin persistencia: el PDF y el Markdown no se guardan en disco ni en base de datos.
- Nuevo feature `documentos` en `app/src/api/documentos/` siguiendo el Feature Layer Cascade (Router → Controller → Service → Mapper; sin Repository).
- Nuevas dependencias en `requirements.txt`: `pymupdf` 2.x (incluye el conversor a Markdown que antes era `pymupdf4llm` y un modelo de layout con `onnxruntime`) para la conversión y `pytest` para las pruebas.

## Capabilities

### New Capabilities
- `conversion-pdf-markdown`: convertir un PDF con texto a Markdown a través de la API, incluyendo validación de entrada y errores.

### Modified Capabilities
<!-- Ninguna: no existen specs previas. -->

## Impact

- **Código**: nuevo `app/src/api/documentos/`; `app/main.py` registra el router del feature.
- **API**: nuevo endpoint `POST /documentos/convertir`.
- **Dependencias**: `pymupdf` 2.x (~250 MB con sus dependencias de layout; licencia AGPL-3.0, aceptada por el usuario: si la API se ofrece públicamente, el código fuente debe publicarse) y `pytest`.
- **Fuera de alcance**: OCR, otros formatos (docx, imágenes), guardar resultados, extraer imágenes del PDF.

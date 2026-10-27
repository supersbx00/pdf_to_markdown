# Proposal

## Why

Hoy `POST /documentos/convertir` devuelve el Markdown dentro de un JSON: no se puede descargar como archivo y se pierden las imágenes del PDF. Además, en documentos largos falta un índice para navegar. El usuario necesita bajar el documento convertido con su formato completo: títulos, índice e imágenes.

## What Changes

- Nuevo endpoint `POST /documentos/descargar`. Recibe el mismo PDF (campo `archivo`) y devuelve un `.zip` descargable con:
  - `<nombre>.md`: el Markdown con un **índice al inicio** (links a cada sección) y los títulos jerarquizados (`#`, `##`, `###`…).
  - `imagenes/`: las imágenes extraídas del PDF (PNG), referenciadas desde el `.md` con rutas relativas.
- El índice se arma con los marcadores del PDF. Si el PDF no tiene marcadores, se arma con los títulos detectados en el Markdown.
- Se descartan las imágenes chicas (logos, íconos, decoraciones): las que miden menos del 5% del ancho o del alto de su página.
- Se elimina del `.md` el índice que trae el propio PDF (la sección "Índice/Contenido/Tabla de contenidos" y las líneas con puntos guía y número de página). Queda solo el índice generado, con links.
- Los bloques de código o comandos en fuente normal, donde todas las líneas son comandos de terminal Linux/Mac o código, van a un bloque ` ``` `. El código en fuente monoespaciada ya sale así. Esto aplica solo a `/descargar`.
- Se mantienen las mismas validaciones de `/convertir` (400, 413, 422) y la regla de no persistir: todo se procesa en memoria.
- `POST /documentos/convertir` **no cambia**: sigue devolviendo el JSON actual.

## Capabilities

### New Capabilities

_(ninguna)_

### Modified Capabilities

- `conversion-pdf-markdown`: se agregan requirements para la descarga en `.zip` (con imágenes e índice) sin modificar los existentes.

## Impact

- Código: `app/src/api/documentos/` (router, controller, service, mapper). No se agrega Repository porque no hay persistencia.
- API: endpoint nuevo `POST /documentos/descargar` (`application/zip`). Sin cambios incompatibles.
- Dependencias: ninguna nueva (`zipfile`, `base64` y `re` son stdlib, más `pymupdf` que ya está instalado).
- Tests: nuevos casos en `tests/test_documentos.py`.

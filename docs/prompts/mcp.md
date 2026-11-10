# Prompt: exponer la API como servidor MCP

## Contexto
- API FastAPI con un único feature `documentos` en `app/src/api/documentos/` (router → controller → service → mapper, sin repository).
- `POST /documentos/convertir` recibe un PDF por multipart (`UploadFile`) y devuelve `{archivo, paginas, markdown}`.
- Un cliente MCP envía argumentos JSON, no multipart, así que ese endpoint no sirve tal cual como tool.
- Rama: `feature/mcp` (desde `dev`).

## Tarea
Agregar `fastapi-mcp` y exponer una sola tool MCP, "convertir PDF a Markdown", que recibe el PDF en base64 y reutiliza el service existente.

## Restricciones
- Dependencia nueva: `fastapi-mcp` en `requirements.txt`. La versión y la API de montaje (`FastApiMCP(...)`, `mount_http()` o equivalente) se verifican contra la librería instalada, no de memoria.
- Endpoint nuevo en el feature `documentos`:
  - **Router:** `POST /documentos/convertir-base64` con `operation_id="convertir_pdf_base64"` y un body Pydantic `{nombre: str, contenido_base64: str}`.
  - **Controller:** decodifica el base64 (inválido → 400) y llama a `service.convertir(nombre, contenido)`. Aplica la regla de excepciones de `architecture.md`.
  - **Service y mapper:** no se tocan. La validación de 20 MB, PDF válido, contraseña y PDF sin texto ya está ahí.
- Montaje MCP en `app/main.py`, en `/mcp`, filtrado para exponer **solo** `convertir_pdf_base64`.
- No se tocan `/documentos/convertir` ni `/documentos/descargar`, ni se exponen por MCP.
- Sin autenticación, caché ni repository.

## Formato
`POST /documentos/convertir-base64`

Request:
```json
{"nombre": "guia.pdf", "contenido_base64": "JVBERi0xLjcK..."}
```

Response 200:
```json
{"archivo": "guia.pdf", "paginas": 3, "markdown": "# ..."}
```

| Código | Cuándo |
|---|---|
| 400 | base64 inválido, no es PDF, PDF dañado o con contraseña |
| 413 | supera 20 MB una vez decodificado |
| 422 | body mal formado (FastAPI) o PDF sin texto extraíble |
| 500 | error no controlado |

Tool MCP: `convertir_pdf_base64`, con los mismos argumentos y la misma respuesta.

## Verificación
**Revisa Claude:**
- `pytest -q` antes (línea base) y después.
- Tests nuevos del endpoint: éxito, base64 inválido → 400 y no-PDF → 400.
- Test de que `/mcp` lista solo la tool `convertir_pdf_base64`.
- Revisar el diff y pasar el checklist del Auditor.

**Pruebas tú:**
1. `uvicorn app.main:app --port 8000` y abrir `http://localhost:8000/docs`: aparece `convertir-base64`.
2. `curl -X POST localhost:8000/documentos/convertir-base64 -H 'Content-Type: application/json' -d "{\"nombre\":\"x.pdf\",\"contenido_base64\":\"$(base64 -w0 x.pdf)\"}"` → devuelve el Markdown.
3. `claude mcp add --transport http documentos http://localhost:8000/mcp`. En Claude Code, `/mcp` muestra el servidor con una sola tool; pedirle que convierta un PDF.

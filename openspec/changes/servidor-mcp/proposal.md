# Proposal

## Why

La conversión de PDF a Markdown hoy solo se usa por HTTP. Queremos que un cliente MCP (por ejemplo, Claude Code) la invoque como tool. `POST /documentos/convertir` recibe multipart, y un cliente MCP envía argumentos JSON, así que hace falta una entrada JSON con el PDF en base64 y un servidor MCP que la exponga.

## What Changes

- Nuevo endpoint `POST /documentos/convertir-base64` (`operation_id="convertir_pdf_a_md"`) que recibe `{nombre, contenido_base64}` y devuelve la misma respuesta que `/documentos/convertir` (`{archivo, paginas, markdown}`), reutilizando `service.convertir`.
- Un base64 inválido responde 400. El resto de las validaciones (20 MB, firma PDF, dañado, contraseña, sin texto) las sigue haciendo el service, con los mismos códigos.
- Nueva dependencia `fastapi-mcp` (0.4.x). El servidor MCP se monta en `/mcp` (transporte HTTP) y expone **solo** la tool `convertir_pdf_a_md`.
- `/documentos/convertir` y `/documentos/descargar` no cambian y no quedan expuestos como tools MCP.
- Sin autenticación, caché ni repository.

## Capabilities

### New Capabilities
- `servidor-mcp`: exposición de la API como servidor MCP en `/mcp` y qué operaciones se publican como tools.

### Modified Capabilities
- `conversion-pdf-markdown`: se agrega la conversión de un PDF recibido como base64 en JSON (`POST /documentos/convertir-base64`), con las mismas validaciones que la conversión multipart.

## Impact

- **Código:** `app/src/api/documentos/documentos_router.py` (endpoint y body Pydantic), `app/src/api/documentos/documentos_controller.py` (decodificar el base64 y delegar), `app/main.py` (montaje MCP). El service y el mapper no cambian.
- **Dependencias:** `fastapi-mcp` en `requirements.txt`, que también instala `mcp`, `httpx`, `pydantic-settings`, `rich` y `typer`, entre otras.
- **API:** un endpoint nuevo y la ruta `/mcp`. Los endpoints existentes se mantienen como están.
- **Tests:** nuevos en `tests/test_documentos.py` (o en un archivo nuevo para el MCP).

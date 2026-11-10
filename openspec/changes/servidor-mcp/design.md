# Design

## Context

- El feature `documentos` vive en `app/src/api/documentos/` (router → controller → service → mapper, sin repository). `service.convertir(nombre, contenido: bytes)` ya valida 20 MB, la firma `%PDF-`, PDF dañado, contraseña y texto extraíble, y levanta `HTTPException` (400/413/422).
- `app/main.py` crea la `FastAPI` e incluye el router. No hay `lifespan` ni `src/config/` en este proyecto.
- `fastapi-mcp` 0.4.0 (la última en PyPI, revisada desde el wheel): `FastApiMCP(app, include_operations=[...])` lee el OpenAPI de la app **al construirse**, `mount_http(mount_path="/mcp")` registra el transporte HTTP y `mcp.tools` expone la lista filtrada. Las tools se ejecutan llamando a la propia app por ASGI. Si la respuesta es un 4xx/5xx, devuelve un error con `response.text`, que incluye el `detail`.

## Goals / Non-Goals

**Goals:**
- Un endpoint JSON que reutilice `service.convertir` sin duplicar validaciones.
- Un servidor MCP que exponga solo ese endpoint.

**Non-Goals:**
- Transporte SSE, autenticación del MCP, límite de tamaño previo a la decodificación y streaming del base64.

## Decisions

1. **El body Pydantic `ConvertirPdfAMdRequest` va en `documentos_router.py`.** El router es el que define el contrato del endpoint, y un modelo de un solo uso no justifica un archivo nuevo. No se usa `documentos_model.py` porque la arquitectura lo reserva para un ORM. *Alternativa:* `documentos_schema.py`. Se descartó porque no es una capa definida y Ponytail pide el mínimo.

2. **El base64 se decodifica en el controller con `base64.b64decode(..., validate=True)`.** Convertir el formato de entrada HTTP a bytes es parte del ciclo request/response, igual que hoy el controller hace `await archivo.read()`. Un `binascii.Error` se traduce a `HTTPException(400, "El contenido no es base64 válido")`. El controller sigue la regla de excepciones: re-lanza los `HTTPException` y envuelve el resto en un 500. *Alternativas:* el service, pero lo obligaría a conocer el formato de transporte; el mapper, pero no puede levantar `HTTPException`. Ambas se descartaron.

3. **`validate=True`** rechaza los caracteres fuera del alfabeto en vez de ignorarlos en silencio, como hace el modo por defecto. Así un base64 roto no llega a la conversión como basura.

4. **El montaje MCP se hace en `app/main.py`, después de `include_router`:** `FastApiMCP(app, include_operations=["convertir_pdf_a_md"]).mount_http(mount_path="/mcp")`. Debe ir después porque la librería toma el OpenAPI al construirse. Se usa `include_operations` (lista blanca) en vez de `exclude_operations` para que un endpoint nuevo no se publique por accidente.

5. **Se usa `mount_http` y no `mount`/`mount_sse`.** HTTP streamable es el transporte que espera `claude mcp add --transport http`, y `mount()` está deprecado en la 0.4.

6. **Dependencia:** `fastapi-mcp>=0.4,<0.5` en `requirements.txt`, con el mismo estilo de rango que `pymupdf`. También se fija `mcp>=1.12,<2`: `fastapi-mcp` 0.4.0 declara `mcp>=1.12` sin tope, y `mcp` 2.x cambió la firma de `Server.__init__` (la app falla al arrancar con un `TypeError`). Se detectó durante el apply.

## Risks / Trade-offs

- [Un payload base64 enorme se decodifica entero antes de que el service rechace los >20 MB] → Se acepta. El límite de 20 MB ya existe y es una API interna sin auth. Si molesta, se agrega `max_length` al campo (~27 MB en base64) en un change aparte.
- [`fastapi-mcp` trae muchas dependencias transitivas (mcp, httpx, rich, typer...)] → Se acepta. Es la librería que eligió el usuario.
- [El `operation_id` es el contrato de la tool: si se renombra, la tool desaparece del MCP] → Lo cubre un test que lista `mcp.tools`.
- [Sin auth, cualquiera con acceso de red a `/mcp` puede convertir PDFs] → Es igual que los endpoints actuales, que tampoco tienen auth.

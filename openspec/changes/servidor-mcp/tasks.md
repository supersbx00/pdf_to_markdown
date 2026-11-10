# Tasks

## 1. Línea base y dependencia

- [x] 1.1 Correr `pytest -q` antes de tocar código y anotar el resultado como línea base. Si algún test ya fallaba, se reporta como preexistente
- [x] 1.2 Agregar `fastapi-mcp>=0.4,<0.5` a `requirements.txt` e instalarlo. Verificar con `pip show fastapi-mcp` y con `python -c "from fastapi_mcp import FastApiMCP"`. Antes de usarlas, confirmar que `include_operations`, `mount_http` y `.tools` existen en la versión instalada

## 2. Endpoint `POST /documentos/convertir-base64`

- [x] 2.1 En `documentos_router.py`, agregar el modelo `ConvertirPdfAMdRequest(nombre: str, contenido_base64: str)` y el endpoint `POST /convertir-base64` con `operation_id="convertir_pdf_a_md"`, que delega en `controller.convertir_pdf_a_md(body)`
- [x] 2.2 En `documentos_controller.py`, agregar `convertir_pdf_a_md(body)`: decodifica con `base64.b64decode(..., validate=True)`, traduce `binascii.Error` a `HTTPException(400, "El contenido no es base64 válido")`, llama a `service.convertir(body.nombre, contenido)`, re-lanza los `HTTPException` y envuelve el resto en un 500. El service y el mapper no se tocan
- [x] 2.3 Agregar tests en `tests/test_documentos.py`: PDF válido en base64 → 200 con `archivo`, `paginas` y `markdown`; base64 inválido → 400; base64 de texto plano → 400 "no es un PDF válido"; body sin `contenido_base64` → 422. Verificar con `pytest -q` que pasen todos, incluidos los existentes

## 3. Servidor MCP

- [x] 3.1 En `app/main.py`, después de `include_router`, crear `FastApiMCP(app, include_operations=["convertir_pdf_a_md"])` y montarlo con `mount_http(mount_path="/mcp")`
- [x] 3.2 Agregar un test que importe el objeto MCP desde `app.main` y verifique que `[t.name for t in mcp.tools] == ["convertir_pdf_a_md"]`. Verificar con `pytest -q`

## 4. Verificación de integración

- [x] 4.1 Correr `pytest -q` completo y compararlo con la línea base: los tests nuevos pasan y no hay regresiones
- [x] 4.2 Revisar el diff con el checklist del Agente Auditor (dependencias reales, archivos en el feature, capas sin invasiones, regla de excepciones) y reportar los hallazgos en una sola pasada

## Workflow follow-up

- Prueba manual del usuario: `uvicorn app.main:app --port 8000`, confirmar que `convertir-base64` aparece en `/docs`, llamarlo con `curl` usando un PDF en base64 y registrar el servidor con `claude mcp add --transport http documentos http://localhost:8000/mcp` (en `/mcp` debe verse una sola tool).
- Con la prueba manual aprobada, `/opsx:archive`.

# Principios SOLID adaptados a FastAPI

**Precedencia:** `architecture.md` decide qué capas existen y Ponytail cuánto código va en cada una. Si un principio pide una clase, interfaz, ABC, `Protocol` o inyección que el feature no necesita hoy, no se aplica. SOLID es una guía para escribir y revisar, no una razón para agregar código. El Agente Auditor lo anota como sugerencia, no como rechazo.

## S · Una responsabilidad
Cada función hace una sola cosa, y cada capa solo lo suyo. El Service orquesta en pasos cortos; cada paso es una llamada.
```python
# documentos_service.py
async def descargar(nombre: str, contenido: bytes) -> tuple[str, bytes]:
    _validar(contenido)
    toc, chunks, tamanos, lineas = await run_in_threadpool(_pdf_to_chunks, contenido)
    markdown, imagenes = armar_markdown(chunks, tamanos, lineas)
    ...
```

## O · Abierto a extender, cerrado a modificar
Un caso nuevo se agrega con una fila en un set, dict o tupla de datos, no con otro `if` en una cadena que ya existe.
```python
# documentos_mapper.py: un comando nuevo es una entrada más, _es_codigo no se toca
COMANDOS = {"pip", "python", "git", ..., "uv"}
```

## L · Sustitución
Una función que reemplaza a otra (o una dependencia sobreescrita en tests con `app.dependency_overrides`) respeta la misma firma, el mismo tipo de retorno y los mismos `HTTPException`. Un mock que devuelve otra forma de dato no sirve como reemplazo.
```python
# Si _pdf_to_markdown devuelve (paginas, markdown), su mock también
monkeypatch.setattr(service, "_pdf_to_markdown", lambda c: (1, "# Hola"))
```

## I · Contratos pequeños
Cada función recibe solo los datos que usa, no el objeto entero. El Mapper recibe dicts y valores, no el `UploadFile` ni el `pymupdf.Document`.
```python
def to_conversion_response(archivo: str, paginas: int, markdown: str) -> dict:   # no (archivo: UploadFile, doc)
```

## D · Depender de lo estable
Las capas dependen de la de abajo, nunca de la de arriba. Clientes y configuración llegan por `Depends` o como parámetro desde `app/src/config/`, no como global que se fija antes de la llamada ni como cliente creado dentro del feature. Los valores van en `settings` o en una constante con nombre, no como número mágico.
```python
redis: Redis = Depends(get_redis_client)   # no redis.Redis(host=...) dentro del Repository
MAX_BYTES = 20 * 1024 * 1024               # no if len(contenido) > 20971520
```

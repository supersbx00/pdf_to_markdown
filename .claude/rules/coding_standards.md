# CODING_STANDARDS.md - Estándares de Código y Patrones de Desarrollo

## 1. Calidad y Estilo
- **Ponytail**: el código dentro de cada capa sigue la skill `/ponytail` (mínimo código que funciona, stdlib antes que dependencias, sin abstracciones especulativas). Ponytail no decide qué capas existen: eso lo define `architecture.md`. El Agente Auditor señala los incumplimientos en una sola pasada; no rechaza ni re-itera automáticamente.

## 2. Definición de Queries (SQL/GraphQL)
- Toda query debe definirse como un **string local dentro de la función** que la utiliza. 
- **Prohibido**: Declarar queries como constantes globales al inicio del archivo. Cada función debe ser autocontenida y leerse de arriba a abajo.

```python
# MAL
QUERY_ASSET_DETALLE = """..."""

async def get_asset_detalle(...):
    ...

# BIEN
async def get_asset_detalle(...):
    query = """..."""
    ...
```

## 3. Utilidades Compartidas
- Las funciones puras que son utilizadas por más de un feature no se duplican. 
- Deben ubicarse en el directorio `src/shared/`.
- No se debe crear una función compartida de manera preventiva; solo se mueve a `shared/` cuando un segundo feature demuestra necesitarla.

## 4. Manejo de Caché y Persistencia
Si un feature implementa caché (ej. Redis), debe seguir estas reglas:
- **Timeouts Duros**: Todo lo que toque red o caché debe tener un timeout establecido. Un fallo en el caché debe degradar el servicio (ir a la fuente original (hoy Dagster) o retornar null en campos opcionales), pero **nunca** debe romper el endpoint retornando un Error 500 general si existen vías secundarias.
- **Versionado de Claves**: Las claves de caché deben tener una estructura versionada y estandarizada (ej. `v1:entidad:id`). Si cambia la estructura de los datos guardados, se sube la versión para invalidar datos viejos.
- **Publicación Atómica**: Las escrituras en caché de estructuras complejas deben hacerse mediante transacciones para evitar guardar estados parciales.

## 5. Independencia de Componentes
Si un feature no necesita persistencia (no lee BD, no cachea), simplemente **no lleva archivo Repository**. La arquitectura es modular y se adapta a las necesidades de cada endpoint sin forzar la creación de archivos vacíos.
# Arquitectura: Feature Layer Cascade

Todo módulo se agrupa por feature en `src/api/<feature>/`, y cada archivo se nombra `<feature>_<capa>.py` con guion bajo (ej. `src/api/assets/assets_router.py`). Nunca con punto (`assets.router.py`): Python no puede importar un módulo con punto en el nombre. La estructura sigue un flujo unidireccional estricto: **Router -> Controller -> Service -> Repository -> Mapper**.

## Responsabilidades Estrictas por Capa:

1. **Router (`<feature>_router.py`)**
   - Únicamente define el endpoint (verbos HTTP, paths, dependencias de FastAPI).
   - Delega inmediatamente la ejecución al Controller. Cero lógica de negocio.

2. **Controller (`<feature>_controller.py`)**
   - Maneja el ciclo request/response HTTP.
   - Orquesta la llamada al Service.
   - **Regla de Excepciones**: Si el Service levanta un `HTTPException` específico (ej. 404, 400), el Controller lo re-lanza intacto. Solo envuelve en un Error 500 las excepciones no controladas.
     ```python
     async def get_algo(...):
         try:
             return await service.get_algo(...)
         except HTTPException:
             raise
         except Exception as e:
             raise HTTPException(status_code=500, detail=str(e))
     ```

3. **Service (`<feature>_service.py`)**
   - Contiene la lógica de negocio pura y orquestación de llamadas HTTP a APIs externas.
   - **Regla Estricta**: No importa conexiones de bases de datos ni cachés directamente. Si necesita persistencia o caché, debe llamar al Repository. No sabe de SQL ni de Redis.

4. **Repository (`<feature>_repository.py`)**
   - Única capa autorizada para la persistencia de datos (PostgreSQL, MySQL, Redis, etc.).
   - Si una función toca un motor de datos (aunque sea una sola línea), va aquí.
   - Retorna diccionarios o records crudos, no objetos HTTP.

5. **Mapper (`<feature>_mapper.py`)**
   - Funciones **puras** (sin I/O, sin llamadas a red, BD o caché).
   - Se encarga de transformar, aplanar, filtrar o combinar datos en memoria para darles la forma final de respuesta de la API.
   - No levanta `HTTPException` ni decide si cachear o ir a Dagster: eso es Service (orquestación) o Repository (qué se persiste).

*(Opcional)* **Model (`<feature>_model.py`)**: Solo se implementa si se especifica el uso de un ORM en lugar de SQL puro o diccionarios.
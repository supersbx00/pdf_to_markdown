# Contexto: Prompt en Archivo y Uso Eficiente del Contexto

## 1. Prompt en Archivo (antes del proposal)
- **Consulta obligatoria:** nunca se modifica ni genera código (`.py`), configuración ni documentación (`.md`) sin un prompt previo aprobado explícitamente por el usuario.
- **Dónde va:** terminadas las preguntas del protocolo de `CLAUDE.md`, Claude escribe el prompt en `docs/prompts/<tarea>.md` (kebab-case), no en el chat. Lleva solo las piezas necesarias de:
  - **Contexto:** estado actual, feature y archivos involucrados.
  - **Tarea:** qué se pide, en una o dos frases.
  - **Restricciones:** capas afectadas, reglas de `.claude/rules/` que aplican, lo que no se toca.
  - **Formato:** contrato del endpoint (método, path, request, response, códigos de error).
  - **Verificación:** separada en dos bloques:
    - *Revisa Claude:* `pytest`, diff, checklist del Auditor.
    - *Prueba el usuario:* pasos concretos (ej. `curl` o Swagger en `http://localhost:8000/docs` con un archivo dado y la respuesta esperada).
- **Respuesta en chat (corta):**
  1. Primera línea: "No apliqué nada, falta tu aprobación."
  2. Resumen de una línea y la ruta del `.md`.
  3. Los riesgos o supuestos que el usuario deba saber.
  4. La pregunta de aprobación.
- **Revisión:** el usuario puede editar el `.md` en su IDE o corregir por chat. Claude **relee el archivo** antes de seguir.
- **Si el resultado no es el esperado:** primero se revisa qué pieza del prompt faltó o estaba mal, se corrige el `.md` y recién después el código.
- **Aprobación:** el proposal de OpenSpec (`/opsx:propose`) se genera solo con el prompt aprobado, y se basa en él.
- **Excepción:** no aplica a consultas, commits ni tareas de git.

## 2. Optimización de Contexto
- **Consultas ligeras:** antes de leer código, ubicar con `grep`/`find` acotados al feature (`app/src/api/<feature>/`) y leer solo las funciones o líneas necesarias, no archivos completos.
- **Indexación selectiva:** leer únicamente las capas del feature involucrado en la tarea y lo que importan de `app/src/config/` o `app/src/shared/`. No se recorre el resto de features "por si acaso".
- **Grafo del repo:** si existe `.graphify/GRAPH_REPORT.md`, se usa para ubicar funciones y dependencias antes de abrir archivos. Antes de confiar en él, comparar su commit con `git rev-parse HEAD`; si no coincide, tomarlo solo como orientación.
- **Archivos pesados:** no cargar en contexto PDFs, ZIPs, binarios ni salidas largas de tests; filtrar (`pytest -q`, `tail`, `grep`) y mostrar solo lo relevante.
- **Subagentes con medida:** no lanzar subagentes salvo que la tarea lo justifique (ej. una auditoría de todo el proyecto) y el usuario lo apruebe; cada uno parte de cero y gasta mucho.

# documentos_md_uaysen

API en **FastAPI** que convierte documentos **PDF a Markdown**. Sirve para pasar apuntes, guías o manuales en PDF a texto estructurado que se puede editar, versionar o procesar con otras herramientas (por ejemplo, darlo como contexto a una IA).

- Conserva la estructura: los títulos del PDF salen como encabezados `#`, `##`, `###`…
- Extrae las imágenes relevantes (descarta logos e íconos chicos).
- Genera un índice con links al inicio del documento y elimina el índice original del PDF.
- Detecta bloques de código o comandos de terminal y los deja en bloques ` ``` `.
- Todo se procesa en memoria: **no guarda** el PDF ni el Markdown en el servidor.
- No hace OCR: los PDF escaneados (sin texto) se rechazan.

## Endpoints

| Método | Ruta | Qué hace |
|---|---|---|
| `GET` | `/` | Health check: `{"status": "ok"}` |
| `POST` | `/documentos/convertir` | Recibe el PDF y responde un JSON con `archivo`, `paginas` y `markdown` |
| `POST` | `/documentos/descargar` | Recibe el PDF y responde un `.zip` con `<nombre>.md` + carpeta `imagenes/` |

Ambos `POST` reciben el archivo como `multipart/form-data` en el campo `archivo`.

| Código | Cuándo |
|---|---|
| `400` | El archivo no es un PDF, está dañado o tiene contraseña |
| `413` | El archivo supera los 20 MB |
| `422` | El PDF no tiene texto extraíble (escaneado) |

Ejemplos:

```bash
# Markdown en JSON
curl -F "archivo=@mi_documento.pdf" http://localhost:8000/documentos/convertir

# Zip con el .md y sus imágenes
curl -F "archivo=@mi_documento.pdf" -OJ http://localhost:8000/documentos/descargar
```

La documentación interactiva (Swagger) queda en <http://localhost:8000/docs>: desde ahí se puede subir un PDF y probar los endpoints sin usar `curl`.

## Correr con Docker

Requisito: Docker con Docker Compose.

```bash
docker compose up --build
```

La API queda en <http://localhost:8000>. El `docker-compose.yml` monta `./app` dentro del contenedor y corre `fastapi dev`, así que los cambios en el código se recargan solos.

Para una imagen de producción (sin recarga, usa el `CMD` del `Dockerfile`):

```bash
docker build -t documentos-md .
docker run -p 8000:8000 documentos-md
```

### Sin Docker

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
fastapi dev app/main.py
```

### Tests

```bash
pytest
```

## Estructura

El proyecto sigue la arquitectura **Feature Layer Cascade**: cada feature vive en `app/src/api/<feature>/` y se separa en capas con un flujo de una sola dirección, **Router → Controller → Service → Repository → Mapper**.

```
app/
├── main.py                         # crea la app FastAPI y registra los routers
└── src/api/documentos/
    ├── documentos_router.py        # define los endpoints
    ├── documentos_controller.py    # maneja request/response y errores HTTP
    ├── documentos_service.py       # validaciones y conversión con PyMuPDF
    └── documentos_mapper.py        # funciones puras: índice, imágenes, código, zip
tests/                              # pruebas con pytest
openspec/                           # specs y changes de OpenSpec
.claude/                            # reglas, comandos y skills para Claude Code
.devcontainer/                      # entorno de desarrollo con Claude Code
```

`documentos` no usa base de datos ni caché, por eso no tiene Repository. Las reglas completas están en `.claude/rules/architecture.md` y `.claude/rules/coding_standards.md`.

## Desarrollo con IA: Devcontainer + Claude Code + OpenSpec

El proyecto está preparado para programar con IA de forma ordenada: la IA no escribe código "a la rápida", sino que primero acuerda un plan escrito (spec-driven development) y recién después implementa.

### Devcontainer

`.devcontainer/devcontainer.json` arma un entorno listo para trabajar:

- Imagen de Python con Node.js LTS.
- Instala **Claude Code** (`@anthropic-ai/claude-code`) y las dependencias de `requirements.txt` al crear el contenedor.
- Trae las extensiones de VS Code de Python, Pylance y Claude Code.

Para usarlo: abrir la carpeta en VS Code (con la extensión *Dev Containers*) → **Reopen in Container**. Dentro del contenedor, correr `claude` en la terminal e iniciar sesión.

El devcontainer usa Python 3.13, igual que el `Dockerfile`, y reenvía el puerto 8000. Dentro del contenedor, `fastapi dev app/main.py` deja la API en <http://localhost:8000>, igual que con Docker Compose (no los corras a la vez, porque chocan en el puerto).

### Claude Code

`CLAUDE.md` y `.claude/rules/` le dicen a Claude cómo trabajar en este repo:

- **Arquitectura** (`architecture.md`): qué va en cada capa y cómo se nombran los archivos.
- **Estándares** (`coding_standards.md`): código mínimo, sin dependencias ni abstracciones innecesarias.
- **Git** (`git.md`): ramas `feature/`, `fix/`, `chore/`… que salen de `dev`; commits en Conventional Commits en español; Claude nunca hace `push`.
- **Flujo** (`workflow.md`): un feature a la vez.

Cuando se le pide un feature nuevo, Claude actúa en roles: **Builder** (hace preguntas y planifica), **Auditor** (revisa el plan y el código buscando errores o desvíos de la arquitectura) y **Tester** (escribe las pruebas).

### OpenSpec (spec-driven)

[OpenSpec](https://github.com/Fission-AI/OpenSpec) guarda los requerimientos como specs en Markdown dentro del repo, así la IA y las personas trabajan sobre el mismo contrato:

- `openspec/specs/`: lo que el sistema hace hoy (por ejemplo, `conversion-pdf-markdown/spec.md`).
- `openspec/changes/`: cambios propuestos (`proposal.md`, `design.md`, `tasks.md` y el delta de specs).
- `openspec/changes/archive/`: cambios ya implementados.

El ciclo, con los comandos de Claude Code en `.claude/commands/opsx/`:

1. **Preguntas**: describes el feature y Claude hace entre 3 y 10 preguntas, de a una, para aclararlo (incluida la rama).
2. **`/opsx:propose`**: Claude genera el proposal (por qué, qué cambia, diseño y tareas). Ese es el plan.
3. **Apruebas** el proposal (o pides cambios con `/opsx:update`).
4. **`/opsx:apply`**: Claude implementa las tareas y corre los tests.
5. **`/opsx:archive`**: se archiva el change y sus specs pasan a `openspec/specs/`.

También está `/opsx:explore` para pensar una idea antes de proponerla.

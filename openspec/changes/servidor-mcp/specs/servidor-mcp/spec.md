# Spec Delta

## Purpose

Expone la conversión de PDF a Markdown como servidor MCP, para que un cliente MCP (por ejemplo, Claude Code) la invoque como tool sin pasar por multipart.

## ADDED Requirements

### Requirement: Servidor MCP en /mcp
El sistema SHALL servir un servidor MCP por transporte HTTP en la ruta `/mcp` de la misma aplicación, sin autenticación.

#### Scenario: Cliente MCP se conecta
- **WHEN** un cliente MCP se registra contra `http://<host>/mcp` con transporte HTTP
- **THEN** la conexión se establece y el cliente puede listar las tools

### Requirement: Solo se publica la tool de conversión PDF a Markdown
El servidor MCP SHALL publicar como única tool `convertir_pdf_a_md`, con los argumentos `nombre` y `contenido_base64` y la misma respuesta que `POST /documentos/convertir-base64`. Las demás operaciones de la API (`/documentos/convertir`, `/documentos/descargar`, `/`) MUST NOT publicarse como tools.

#### Scenario: Listado de tools
- **WHEN** un cliente MCP lista las tools del servidor
- **THEN** recibe exactamente una tool, llamada `convertir_pdf_a_md`

#### Scenario: Invocar la tool
- **WHEN** un cliente MCP invoca `convertir_pdf_a_md` con un PDF con texto en base64
- **THEN** recibe `archivo`, `paginas` y `markdown` del documento

#### Scenario: Invocar la tool con un archivo inválido
- **WHEN** un cliente MCP invoca `convertir_pdf_a_md` con un contenido que no es PDF
- **THEN** recibe el error con el mismo mensaje que daría el endpoint HTTP

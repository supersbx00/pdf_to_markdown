# Spec Delta

## ADDED Requirements

### Requirement: Convertir PDF recibido en base64
El sistema SHALL exponer `POST /documentos/convertir-base64`, que recibe un JSON `{nombre, contenido_base64}` con el PDF codificado en base64 y responde 200 con el mismo JSON que `POST /documentos/convertir`: `archivo` (igual a `nombre`), `paginas` y `markdown`. El PDF decodificado pasa por las mismas validaciones que la conversión multipart (tamaño, PDF válido, contraseña, texto extraíble), con los mismos códigos de respuesta.

#### Scenario: PDF en base64 válido
- **WHEN** el cliente envía `{"nombre": "informe.pdf", "contenido_base64": "<PDF de 2 páginas con texto en base64>"}`
- **THEN** el sistema responde 200 con `archivo` igual a `informe.pdf`, `paginas` igual a 2 y `markdown` con el texto del documento

#### Scenario: Contenido decodificado no es PDF
- **WHEN** el cliente envía un `contenido_base64` válido cuyo contenido decodificado es texto plano
- **THEN** el sistema responde 400 con un mensaje que indica que el archivo no es un PDF válido

#### Scenario: PDF decodificado supera 20 MB
- **WHEN** el contenido decodificado supera 20 MB
- **THEN** el sistema responde 413

#### Scenario: Body incompleto
- **WHEN** el cliente envía un JSON sin el campo `contenido_base64`
- **THEN** el sistema responde 422

### Requirement: Rechazar base64 inválido
El sistema SHALL responder 400 cuando `contenido_base64` no es base64 válido, sin intentar convertir.

#### Scenario: Caracteres fuera del alfabeto base64
- **WHEN** el cliente envía `contenido_base64` igual a `"esto no es base64!!"`
- **THEN** el sistema responde 400 con un mensaje que indica que el contenido no es base64 válido

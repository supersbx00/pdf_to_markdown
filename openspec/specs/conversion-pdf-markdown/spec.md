# conversion-pdf-markdown Specification

## Purpose

Permite convertir documentos PDF con texto a Markdown a través de la API, para poder editarlos y procesarlos como texto estructurado.

## Requirements

### Requirement: Convertir PDF a Markdown
El sistema SHALL exponer `POST /documentos/convertir`, que recibe un archivo PDF en el campo `archivo` (multipart/form-data) y responde 200 con un JSON que contiene `archivo` (nombre original), `paginas` (cantidad de páginas) y `markdown` (contenido convertido).

#### Scenario: PDF con texto válido
- **WHEN** el cliente envía un PDF de 2 páginas con texto
- **THEN** el sistema responde 200 con `paginas` igual a 2 y `markdown` con el texto del documento

#### Scenario: Se conserva la estructura
- **WHEN** el cliente envía un PDF con un título en fuente grande y párrafos en fuente normal
- **THEN** el `markdown` contiene el título como encabezado Markdown (línea que comienza con `#`)

### Requirement: Rechazar archivos que no son PDF
El sistema SHALL responder 400 cuando el archivo recibido no es un PDF válido (no comienza con la firma `%PDF-` o no se puede abrir como PDF).

#### Scenario: Archivo de texto
- **WHEN** el cliente envía un archivo `.txt`
- **THEN** el sistema responde 400 con un mensaje que indica que el archivo no es un PDF válido

#### Scenario: PDF corrupto
- **WHEN** el cliente envía un archivo que comienza con `%PDF-` pero cuyo contenido está dañado
- **THEN** el sistema responde 400 con un mensaje que indica que el PDF no se pudo leer

### Requirement: Rechazar PDFs protegidos con contraseña
El sistema SHALL responder 400 cuando el PDF está cifrado y requiere contraseña para abrirse.

#### Scenario: PDF cifrado
- **WHEN** el cliente envía un PDF protegido con contraseña
- **THEN** el sistema responde 400 con un mensaje que indica que el PDF está protegido

### Requirement: Rechazar PDFs sin texto extraíble
El sistema SHALL responder 422 cuando el PDF no contiene texto extraíble (por ejemplo, un documento escaneado), ya que no se realiza OCR.

#### Scenario: PDF escaneado o vacío
- **WHEN** el cliente envía un PDF cuyas páginas no contienen texto
- **THEN** el sistema responde 422 con un mensaje que indica que el PDF no tiene texto extraíble

### Requirement: Limitar el tamaño del archivo
El sistema SHALL responder 413 cuando el archivo supera 20 MB.

#### Scenario: Archivo demasiado grande
- **WHEN** el cliente envía un archivo de más de 20 MB
- **THEN** el sistema responde 413 con un mensaje que indica el tamaño máximo permitido

### Requirement: Sin persistencia
El sistema MUST NOT guardar el PDF recibido ni el Markdown generado en disco ni en base de datos.

#### Scenario: Conversión sin rastro
- **WHEN** el cliente convierte un PDF exitosamente
- **THEN** no quedan archivos nuevos del documento en el servidor

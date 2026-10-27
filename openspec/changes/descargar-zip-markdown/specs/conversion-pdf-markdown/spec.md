# Spec Delta

## ADDED Requirements

### Requirement: Descargar la conversión como zip
El sistema SHALL exponer `POST /documentos/descargar`, que recibe un PDF en el campo `archivo` (multipart/form-data) y responde 200 con un archivo `application/zip` como adjunto, de nombre `<nombre del PDF sin extensión>.zip`. El zip contiene `<nombre>.md` en la raíz y, si hay imágenes, la carpeta `imagenes/`.

#### Scenario: Descarga de un PDF con texto
- **WHEN** el cliente envía `informe.pdf` con texto a `POST /documentos/descargar`
- **THEN** el sistema responde 200 con `Content-Type: application/zip`, `Content-Disposition` de tipo `attachment` con nombre `informe.zip`, y el zip contiene `informe.md` con el texto del documento

#### Scenario: El endpoint JSON no cambia
- **WHEN** el cliente envía el mismo PDF a `POST /documentos/convertir`
- **THEN** el sistema responde el JSON `{archivo, paginas, markdown}` igual que antes

### Requirement: Incluir las imágenes del PDF
El sistema SHALL extraer las imágenes del PDF como archivos PNG dentro de la carpeta `imagenes/` del zip, y el Markdown SHALL referenciarlas con rutas relativas (`![](imagenes/<archivo>.png)`) en el lugar donde aparecen en el documento. El Markdown MUST NOT contener imágenes embebidas en base64.

#### Scenario: PDF con una imagen grande
- **WHEN** el cliente descarga un PDF que tiene una imagen que ocupa un tercio de la página
- **THEN** el zip contiene un PNG en `imagenes/` y el `.md` contiene un link a ese archivo con ruta relativa

#### Scenario: PDF sin imágenes
- **WHEN** el cliente descarga un PDF que solo tiene texto
- **THEN** el zip contiene solo el `.md`, sin carpeta `imagenes/`

### Requirement: Descartar imágenes chicas
El sistema SHALL omitir del zip y del Markdown las imágenes cuyo ancho sea menor al 5% del ancho de su página o cuyo alto sea menor al 5% del alto de su página.

#### Scenario: Ícono pequeño junto a un gráfico
- **WHEN** el cliente descarga un PDF con un ícono de 10×10 puntos y un gráfico de 300×200 puntos en una página A4
- **THEN** el zip contiene solo la imagen del gráfico y el `.md` no tiene referencia al ícono

### Requirement: Índice al inicio desde los marcadores del PDF
Cuando el PDF tiene marcadores, el `.md` del zip SHALL comenzar con una sección de índice que lista cada marcador en orden, indentado según su nivel, como link a la sección del documento que lleva ese título.

#### Scenario: PDF con marcadores
- **WHEN** el cliente descarga un PDF con marcadores "Informe Anual" (nivel 1) e "Introducción" (nivel 2)
- **THEN** el `.md` comienza con un índice donde "Informe Anual" es un link de primer nivel e "Introducción" un link indentado bajo él

### Requirement: Índice desde los títulos cuando no hay marcadores
Cuando el PDF no tiene marcadores, el `.md` del zip SHALL comenzar con un índice armado a partir de los títulos detectados en el Markdown, indentados según su nivel de encabezado y con links a cada sección. Si no se detecta ningún título, el `.md` no lleva índice.

#### Scenario: PDF sin marcadores pero con títulos
- **WHEN** el cliente descarga un PDF sin marcadores cuyo Markdown tiene los títulos "Resumen" y "Resultados"
- **THEN** el `.md` comienza con un índice con links a "Resumen" y "Resultados"

#### Scenario: PDF sin marcadores ni títulos
- **WHEN** el cliente descarga un PDF que solo tiene párrafos de texto normal
- **THEN** el `.md` no contiene sección de índice

### Requirement: Quitar el índice propio del PDF
El `.md` del zip MUST NOT incluir el índice que trae el propio PDF: se elimina la sección cuyo título es Índice, Indice, Contenido(s) o Tabla de contenido(s) (hasta el siguiente título) y toda línea con puntos guía seguidos de un número de página. Esa sección tampoco aparece como entrada en el índice generado.

#### Scenario: PDF con página de índice
- **WHEN** el cliente descarga un PDF cuya primera página es un "Índice" con líneas `1. Introducción ........ 2`
- **THEN** el `.md` contiene un único índice (el generado, con links) y ninguna línea con puntos guía

#### Scenario: Marcador "Índice" en el PDF
- **WHEN** el cliente descarga un PDF cuyos marcadores incluyen una entrada "Índice"
- **THEN** el índice generado no lista esa entrada

### Requirement: Código monoespaciado en bloque de código
En el `.md` del zip, el texto del PDF escrito en fuente monoespaciada SHALL quedar dentro de un bloque de código cercado con ` ``` `, conservando sus saltos de línea.

#### Scenario: Código en Courier
- **WHEN** el cliente descarga un PDF con tres líneas de código en fuente Courier
- **THEN** el `.md` contiene esas tres líneas dentro de un bloque ` ``` `

### Requirement: Comandos y código en fuente normal en bloque de código
En el `.md` del zip, un párrafo del PDF en fuente normal cuyas líneas son todas comandos de terminal Linux/Mac o código de programación SHALL quedar dentro de un bloque ` ``` ` sin etiqueta de lenguaje, una línea por línea original. Un comando dentro de una frase MUST quedar como texto normal.

#### Scenario: Comandos en líneas solas
- **WHEN** el cliente descarga un PDF con un párrafo en Helvetica de dos líneas `pip install fastapi` y `fastapi dev app/main.py`
- **THEN** el `.md` contiene un bloque ` ``` ` con esas dos líneas, cada una en su propia línea

#### Scenario: Comando dentro de una frase
- **WHEN** el cliente descarga un PDF con la frase "luego ejecute pip install para instalar las dependencias"
- **THEN** esa frase queda como texto normal, fuera de un bloque de código

### Requirement: Mismas validaciones y sin persistencia en la descarga
`POST /documentos/descargar` SHALL aplicar las mismas validaciones que `POST /documentos/convertir` (400 si no es PDF, si está dañado o protegido; 413 si supera 20 MB; 422 si no tiene texto extraíble) y MUST NOT guardar en disco el PDF, el Markdown, las imágenes ni el zip.

#### Scenario: Archivo que no es PDF
- **WHEN** el cliente envía un `.txt` a `POST /documentos/descargar`
- **THEN** el sistema responde 400 con un mensaje que indica que el archivo no es un PDF válido

#### Scenario: Descarga sin rastro
- **WHEN** el cliente descarga un PDF con imágenes exitosamente
- **THEN** no quedan archivos nuevos del documento en el servidor

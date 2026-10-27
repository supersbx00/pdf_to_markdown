# Design

## Context

El feature `documentos` (`app/src/api/documentos/`) ya tiene Router → Controller → Service → Mapper y no tiene Repository. El Service valida el PDF (firma `%PDF-`, 20 MB, dañado, contraseña, sin texto) y llama a `doc.to_markdown(use_ocr=False)` de pymupdf 2.x (motor de layout) dentro de `run_in_threadpool`.

Lo que se comprobó en pymupdf 2.0 instalado, con un PDF de prueba:
- `to_markdown(use_ocr=False, embed_images=True, page_chunks=True)` devuelve una lista con un elemento por página: `{"metadata", "toc_items", "page_boxes", "text"}`.
- `page_boxes` trae cada caja con `class` (`"picture"`, `"section-header"`, `"text"`…), su `bbox` en puntos y `pos` (rango `(inicio, fin)` de esa caja dentro de `text`).
- Con `embed_images=True`, cada imagen sale en `text` como `![](data:image/png;base64,...)`. No se escribe nada a disco.
- Los títulos salen como `#`/`##` según el tamaño de fuente, haya o no marcadores. `doc.get_toc()` devuelve `[[nivel, título, página], ...]`.
- Este motor **no** tiene `image_size_limit`: el filtro de imágenes chicas lo hacemos nosotros.

## Goals / Non-Goals

**Goals:**
- Que `/descargar` arme el zip completo en memoria, reutilizando las validaciones de `/convertir` sin duplicarlas.
- Que el `/convertir` actual quede intacto (mismo código y mismos tests en verde).

**Non-Goals:**
- OCR, imágenes en otros formatos que no sean PNG, ni reescribir los niveles de los títulos según los marcadores (se usan los niveles que entrega pymupdf).
- Mover código a `src/shared/`: ningún otro feature lo usa.

## Decisions

### 1. Capas y archivos (todo dentro de `app/src/api/documentos/`)
- **Router**: agrega `@router.post("/descargar")`, que delega a `controller.descargar_pdf(archivo)`.
- **Controller**: `descargar_pdf` lee el archivo, llama a `service.descargar(nombre, contenido)` y envuelve los bytes del zip en `fastapi.Response(media_type="application/zip", headers={"Content-Disposition": ...})`. Re-lanza intacto el `HTTPException` del Service y envuelve todo lo demás en un 500. Armar la respuesta HTTP es trabajo del Controller.
- **Service**: separa las validaciones actuales en `_validar(contenido)` y una apertura común `_abrir(contenido)`, que usan tanto `convertir` como el nuevo `descargar`. `descargar` corre en el threadpool una función que abre el documento y devuelve `(toc, chunks, tamaños_de_página)`. Valida que haya texto (422) y pasa todo al Mapper.
- **Mapper** (funciones puras):
  - `extraer_imagenes(chunks, tamaños)`: recorre las `page_boxes` de tipo `picture` en orden inverso por `pos`, para no correr los offsets. Si la caja mide < 5% del ancho o alto de la página, borra ese tramo del texto. Si no, decodifica el base64 a bytes, lo guarda como `imagenes/pagina{N}_img{K}.png` y reemplaza el tramo por `![](imagenes/pagina{N}_img{K}.png)`. Devuelve `(markdown, {ruta: bytes})`.
  - `armar_indice(markdown, toc)`: si `toc` no está vacío, hace una línea `- [título](#slug)` por marcador, indentada con `(nivel-1)*2` espacios. Si está vacío, usa las líneas `^(#{1,6}) (.+)` del Markdown con el mismo formato. Antepone `## Índice` y la lista. Si no hay entradas, devuelve el Markdown sin cambios.
  - `_slug(título)`: anchor estilo GitHub (minúsculas, quita puntuación salvo `-` y `_`, espacios → `-`, conserva tildes), que es lo que usan GitHub, VS Code y Obsidian.
  - `to_zip(nombre, markdown, imagenes)`: arma el zip con `zipfile.ZipFile(io.BytesIO(), "w", ZIP_DEFLATED)` y devuelve los bytes.
- **Sin Repository**: no hay persistencia (coding_standards §5).

*Alternativa descartada*: `write_images=True` con `image_path` en un directorio temporal. Escribe a disco y rompe el requirement "sin persistencia" aunque después se borre; `embed_images` lo deja todo en memoria.

### 2. Construir el zip en el Mapper
`zipfile` sobre un `BytesIO` es una transformación en memoria (bytes → bytes), sin red, sin disco y sin caché, así que cumple la definición de Mapper puro. Ponerlo en el Service lo mezclaría con la orquestación, y en el Controller le metería lógica de formato.

### 3. Filtro de imágenes con el `bbox` de la caja (en puntos del PDF), no con los píxeles del PNG
El PNG se renderiza a 150 dpi, así que sus píxeles no se comparan directo con el tamaño de la página. El `bbox` y `page.rect` están en la misma unidad. El umbral es 5% (constante del Mapper), según la regla que pidió el usuario.

### 4. Nombre del zip y del `.md`
Se toma el nombre del PDF sin extensión (`Path(nombre).stem`, o `documento` si viene vacío). `Content-Disposition: attachment; filename*=UTF-8''<quote(stem)>.zip` deja pasar tildes y espacios sin romper el header.

### 5. Líneas originales de cada caja de texto (Service)
pymupdf junta las líneas de una caja `text` en un solo párrafo (`pip install fastapi fastapi dev app/main.py`). Para no perder esa información, `_pdf_to_chunks` también saca, por cada caja `text` de cada página, sus líneas con `page.get_text("dict", clip=bbox)` (comprobado: devuelve `["pip install fastapi", "fastapi dev app/main.py"]`) y se las pasa al Mapper junto con los chunks. Se hace dentro del mismo threadpool porque es trabajo de pymupdf sobre el documento ya abierto, en memoria.

### 6. Código y comandos en fuente normal (Mapper, heurística)
`marcar_codigo(chunks, lineas)` reemplaza el tramo `pos` de una caja `text` por un bloque ` ``` ` (sin lenguaje, una línea por línea original) solo si **todas** sus líneas cumplen al menos una de estas condiciones:
- empiezan con `$ `;
- su primera palabra es un comando conocido: pip, pip3, python, python3, git, npm, npx, yarn, node, docker, docker-compose, cd, ls, mkdir, rm, cp, mv, sudo, apt, apt-get, curl, wget, chmod, cat, echo, export, source, uvicorn, fastapi, pytest, brew, ssh, tar;
- empiezan con una palabra clave de código: def, class, import, from…import, function, const, let, var, return, if, for, while, `print(`, `console.`;
- terminan en `{`, `}`, `;` o `):`.

Las cajas que pymupdf ya cercó (monoespaciadas: su texto empieza con ` ``` `) se dejan como están. Se corre antes de `extraer_imagenes`, sobre los mismos `pos`: los reemplazos de ambos se juntan por página y se aplican en orden inverso, así no se corren los offsets. `quitar_indice_pdf(markdown, toc)` se aplica sobre el Markdown ya armado y antes de `armar_indice`. Quita la sección cuyo título (`#…`) es Índice/Indice/Contenido(s)/Tabla de contenido(s) hasta el siguiente título, las líneas que calzan con `\.{4,}\s*\d+\s*$` en cualquier parte, y las entradas del `toc` con esos títulos. Nada de esto toca `/convertir`.

## Risks / Trade-offs

- [Un párrafo que mezcla texto con un comando] → No se marca como código (decisión del usuario: solo líneas solas).
- [Una línea de texto normal que empieza con "cd", "export", "cat"…] → Se puede marcar como código. Mitigación: se exige que todas las líneas de la caja cumplan.
- [Un capítulo real llamado "Contenido"] → Se elimina como si fuera el índice. Es aceptable para la v1.
- [La indentación del código en fuente normal se pierde] → pymupdf no la conserva en fuentes proporcionales; las líneas quedan sin sangría.

- [Marcadores cuyo título no coincide exacto con el título detectado (otra mayúscula, numeración, espacios)] → El link del índice no salta a la sección, pero el texto del índice queda bien. Es aceptable para la v1.
- [Títulos repetidos generan el mismo slug] → GitHub les agrega `-1`, `-2` y nosotros no. El link salta al primero. Es aceptable para la v1.
- [El motor de layout puede marcar como `picture` regiones de gráficos vectoriales] → Salen como PNG renderizados, lo que de hecho es deseable para gráficos y diagramas.
- [Usar `pos` depende de un detalle interno de pymupdf 2.0] → El test con imagen grande y chica lo cubre. Si una versión futura cambia la estructura, el test falla y se ve en seguida. `requirements.txt` ya fija `<3`.
- [Más CPU y memoria por renderizar las imágenes] → Lo acota el límite de 20 MB que ya existe.

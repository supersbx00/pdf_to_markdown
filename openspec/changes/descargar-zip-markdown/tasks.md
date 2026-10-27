# Tasks

## 1. Línea base

- [x] 1.1 Correr `pytest` antes de tocar código y anotar el resultado como línea base (se esperan 8 tests en verde)

## 2. Service: validaciones compartidas

- [x] 2.1 Extraer las validaciones de `convertir` en `_validar(contenido)` y la apertura en `_abrir(contenido)` dentro de `documentos_service.py`, sin cambiar los mensajes ni los códigos. Verificar que los 8 tests existentes de `/convertir` sigan en verde

## 3. Mapper: imágenes, índice y zip

- [x] 3.1 Implementar `extraer_imagenes(chunks, tamaños)` en `documentos_mapper.py` (descarta las cajas `picture` de menos del 5% del ancho o alto de la página y reemplaza el base64 por `![](imagenes/paginaN_imgK.png)`). Verificar con un test unitario que reciba chunks armados a mano con una imagen grande y una chica: solo queda la grande y el texto no contiene `base64`
- [x] 3.2 Implementar `_slug(título)` y `armar_indice(markdown, toc)` (desde los marcadores; si no hay, desde los títulos `#`; sin entradas, el Markdown queda sin cambios). Verificar con tests unitarios los tres casos y un slug con tildes y espacios (`"Introducción General"` → `introducción-general`)
- [x] 3.3 Implementar `to_zip(nombre, markdown, imagenes)`. Verificar con un test unitario que el zip contenga `<nombre>.md` y las rutas `imagenes/...` con los bytes originales

## 4. Endpoint `/descargar`

- [x] 4.1 Agregar `descargar(nombre, contenido)` en el Service (valida, corre en el threadpool la extracción `(toc, chunks, tamaños)` con `use_ocr=False, embed_images=True, page_chunks=True`, valida que haya texto (422) y llama al Mapper)
- [x] 4.2 Agregar `descargar_pdf(archivo)` en el Controller, que devuelve `Response` `application/zip` con `Content-Disposition: attachment; filename*=UTF-8''<stem>.zip`, re-lanza los `HTTPException` y envuelve en 500 lo demás
- [x] 4.3 Agregar `POST /descargar` en el Router, que delega al Controller
- [x] 4.4 Tests de integración en `tests/test_documentos.py`: PDF con texto → 200, zip con `informe.md` y header `informe.zip`; PDF con imagen grande + ícono chico → una sola imagen en `imagenes/` y link relativo en el `.md`; PDF con marcadores → índice con indentación; PDF sin marcadores → índice desde títulos; `.txt` → 400; la descarga no deja archivos en el temp ni en `.`. Verificar que toda la suite (`pytest`) quede en verde

## 5. Índice del PDF y bloques de código

- [x] 5.1 Implementar `quitar_indice_pdf(markdown, toc)` en el Mapper y llamarla antes de `armar_indice` en `descargar`. Verificar con tests unitarios: sección "# Índice" eliminada hasta el siguiente título, líneas con puntos guía eliminadas, y entrada "Índice" del `toc` excluida
- [x] 5.2 En `_pdf_to_chunks`, sacar las líneas de cada caja `text` con `page.get_text("dict", clip=bbox)`. Implementar `marcar_codigo(chunks, lineas)` en el Mapper, combinando sus reemplazos con los de `extraer_imagenes`. Verificar con tests unitarios: caja de comandos → bloque ` ``` ` con una línea por comando; caja de código (`def`, `{`, `;`) → bloque; frase con "pip install" adentro → sin cambios; caja ya cercada → sin cambios
- [x] 5.3 Tests de integración en `tests/test_documentos.py`: PDF con página "Índice" con puntos guía → un solo índice; código en Courier → bloque ` ``` `; comandos en Helvetica en líneas solas → bloque ` ``` ` con dos líneas. Verificar que `pytest` quede completo en verde y que los tests de `/convertir` no cambien

## 6. Verificación manual

- [x] 6.1 Levantar con `fastapi dev app/main.py`, descargar desde `/docs` un PDF real con imágenes, marcadores, página de índice y código, descomprimirlo y revisar que el `.md` se vea bien (índice único, títulos, imágenes, bloques de código) en un visor Markdown

## Workflow follow-up

- Archivar el change con `/opsx:archive` cuando el usuario lo apruebe.

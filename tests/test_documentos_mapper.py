import base64
import io
import zipfile

from app.src.api.documentos.documentos_mapper import (
    _slug,
    armar_indice,
    armar_markdown,
    marcar_codigo,
    quitar_indice_pdf,
    to_zip,
)

A4 = (595.0, 842.0)


def _chunk_con_imagenes() -> dict:
    grande = "\n![](data:image/png;base64," + base64.b64encode(b"GRANDE").decode() + ")\n\n"
    chica = "\n![](data:image/png;base64," + base64.b64encode(b"CHICA").decode() + ")\n\n"
    titulo = "# Informe \n\n"
    texto = chica + titulo + grande
    return {
        "text": texto,
        "page_boxes": [
            {"class": "picture", "bbox": (500, 40, 510, 50), "pos": (0, len(chica))},
            {"class": "section-header", "bbox": (72, 60, 200, 80), "pos": (len(chica), len(chica + titulo))},
            {"class": "picture", "bbox": (72, 200, 372, 400), "pos": (len(chica + titulo), len(texto))},
        ],
    }


def test_extraer_imagenes_descarta_las_chicas():
    markdown, imagenes = armar_markdown([_chunk_con_imagenes()], [A4], [{}])
    assert imagenes == {"imagenes/pagina1_img1.png": b"GRANDE"}
    assert "![](imagenes/pagina1_img1.png)" in markdown
    assert "base64" not in markdown
    assert "# Informe" in markdown


def test_indice_desde_marcadores():
    md = armar_indice("# Informe Anual\n\n## Introducción\n", [[1, "Informe Anual", 1], [2, "Introducción", 1]])
    assert md.startswith("## Índice\n\n- [Informe Anual](#informe-anual)\n  - [Introducción](#introducción)\n")


def test_indice_desde_titulos_sin_marcadores():
    md = armar_indice("# Resumen \n\ntexto\n\n## Resultados \n", [])
    assert md.startswith("## Índice\n\n- [Resumen](#resumen)\n  - [Resultados](#resultados)\n")


def test_sin_titulos_no_hay_indice():
    assert armar_indice("solo un parrafo\n", []) == "solo un parrafo\n"


def test_slug_con_tildes_y_espacios():
    assert _slug("Introducción General") == "introducción-general"
    assert _slug("1. ¿Qué es?") == "1-qué-es"


def test_to_zip_contiene_md_e_imagenes():
    nombre, datos = to_zip("informe.pdf", "# hola", {"imagenes/pagina1_img1.png": b"PNG"})
    assert nombre == "informe.zip"
    with zipfile.ZipFile(io.BytesIO(datos)) as zf:
        assert zf.read("informe.md") == b"# hola"
        assert zf.read("imagenes/pagina1_img1.png") == b"PNG"


def _chunk_texto(*parrafos: str) -> dict:
    texto, cajas = "", []
    for i, p in enumerate(parrafos):
        cajas.append({"index": i, "class": "text", "bbox": (72, 0, 400, 10), "pos": (len(texto), len(texto + p))})
        texto += p
    return {"text": texto, "page_boxes": cajas}


def test_marcar_codigo_comandos_en_bloque():
    chunk = _chunk_texto("Ejecute: \n\n", "pip install fastapi fastapi dev app/main.py \n\n")
    lineas = {0: ["Ejecute:"], 1: ["pip install fastapi", "fastapi dev app/main.py"]}
    markdown, _ = armar_markdown([chunk], [A4], [lineas])
    assert "```\npip install fastapi\nfastapi dev app/main.py\n```" in markdown
    assert markdown.startswith("Ejecute:")


def test_marcar_codigo_detecta_codigo():
    chunk = _chunk_texto("x \n\n")
    lineas = {0: ["function hola() {", "return 1;", "}"]}
    assert marcar_codigo(chunk, lineas) == [(0, 4, "```\nfunction hola() {\nreturn 1;\n}\n```\n\n")]


def test_marcar_codigo_ignora_frases_y_bloques_cercados():
    chunk = _chunk_texto("luego ejecute pip install para instalar \n\n", "```\ndef f():\n```\n\n")
    lineas = {0: ["luego ejecute pip install para instalar"], 1: ["def f():"]}
    assert marcar_codigo(chunk, lineas) == []


def test_quitar_indice_pdf():
    md = "# Índice\n\n1. Intro ........ 2\n\n# Intro\n\ntexto\n\nOtra ....... 4"
    toc = [[1, "Índice", 1], [1, "Intro", 2]]
    limpio, toc_limpio = quitar_indice_pdf(md, toc)
    assert limpio == "# Intro\n\ntexto\n"
    assert toc_limpio == [[1, "Intro", 2]]


def test_titulos_dentro_de_codigo_no_van_al_indice():
    md = armar_indice("# Uso\n\n```\n# comentario\n```\n", [])
    assert "comentario](#" not in md
    assert "- [Uso](#uso)" in md

import io
import os
import zipfile
import tempfile

import pymupdf
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _pdf_con_texto() -> bytes:
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((72, 80), "Informe Anual", fontsize=24)
    page.insert_text((72, 130), "Este es un parrafo de prueba con texto normal.", fontsize=11)
    doc.new_page().insert_text((72, 80), "Segunda pagina del documento.", fontsize=11)
    return doc.tobytes()


def _convertir(contenido: bytes, nombre: str = "doc.pdf", tipo: str = "application/pdf"):
    return client.post("/documentos/convertir", files={"archivo": (nombre, contenido, tipo)})


def test_pdf_con_texto_valido():
    r = _convertir(_pdf_con_texto(), "informe.pdf")
    assert r.status_code == 200
    body = r.json()
    assert body["archivo"] == "informe.pdf"
    assert body["paginas"] == 2
    assert "parrafo de prueba" in body["markdown"]
    assert "Segunda pagina" in body["markdown"]


def test_se_conserva_el_titulo_como_encabezado():
    markdown = _convertir(_pdf_con_texto()).json()["markdown"]
    assert any(linea.startswith("#") and "Informe Anual" in linea for linea in markdown.splitlines())


def test_archivo_de_texto_es_rechazado():
    r = _convertir(b"hola mundo", "notas.txt", "text/plain")
    assert r.status_code == 400
    assert "no es un PDF" in r.json()["detail"]


def test_pdf_corrupto_es_rechazado():
    r = _convertir(b"%PDF-1.7 contenido danado")
    assert r.status_code == 400
    assert "no se pudo leer" in r.json()["detail"]


def test_pdf_cifrado_es_rechazado():
    doc = pymupdf.open()
    doc.new_page().insert_text((72, 72), "secreto")
    cifrado = doc.tobytes(encryption=pymupdf.PDF_ENCRYPT_AES_256, owner_pw="dueno", user_pw="clave")
    r = _convertir(cifrado)
    assert r.status_code == 400
    assert "contraseña" in r.json()["detail"]


def test_pdf_sin_texto_es_rechazado():
    doc = pymupdf.open()
    doc.new_page()
    r = _convertir(doc.tobytes())
    assert r.status_code == 422
    assert "texto extraíble" in r.json()["detail"]


def test_archivo_demasiado_grande_es_rechazado():
    r = _convertir(b"%PDF-" + b"0" * (20 * 1024 * 1024))
    assert r.status_code == 413
    assert "20 MB" in r.json()["detail"]


def test_conversion_no_deja_archivos():
    antes = set(os.listdir(tempfile.gettempdir())), set(os.listdir("."))
    assert _convertir(_pdf_con_texto()).status_code == 200
    despues = set(os.listdir(tempfile.gettempdir())), set(os.listdir("."))
    assert despues == antes


def _descargar(contenido: bytes, nombre: str = "doc.pdf", tipo: str = "application/pdf"):
    return client.post("/documentos/descargar", files={"archivo": (nombre, contenido, tipo)})


def _abrir_zip(r) -> zipfile.ZipFile:
    return zipfile.ZipFile(io.BytesIO(r.content))


def _pdf_con_imagenes(marcadores: bool = False) -> bytes:
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((72, 80), "Informe Anual", fontsize=24)
    page.insert_text((72, 130), "Introduccion", fontsize=16)
    page.insert_text((72, 160), "Texto de la introduccion con varias palabras normales.", fontsize=11)
    grande = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 300, 200), 0)
    grande.set_rect(grande.irect, (200, 30, 30))
    page.insert_image(pymupdf.Rect(72, 200, 372, 400), pixmap=grande)
    icono = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 10, 10), 0)
    icono.set_rect(icono.irect, (0, 0, 255))
    page.insert_image(pymupdf.Rect(500, 40, 510, 50), pixmap=icono)
    if marcadores:
        doc.set_toc([[1, "Informe Anual", 1], [2, "Introduccion", 1]])
    return doc.tobytes()


def test_descargar_devuelve_zip_con_markdown():
    r = _descargar(_pdf_con_texto(), "informe.pdf")
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/zip"
    assert r.headers["content-disposition"] == "attachment; filename*=UTF-8''informe.zip"
    with _abrir_zip(r) as zf:
        assert zf.namelist() == ["informe.md"]
        assert "parrafo de prueba" in zf.read("informe.md").decode()


def test_descargar_incluye_solo_imagenes_grandes():
    with _abrir_zip(_descargar(_pdf_con_imagenes())) as zf:
        imagenes = [n for n in zf.namelist() if n.startswith("imagenes/")]
        markdown = zf.read("doc.md").decode()
    assert imagenes == ["imagenes/pagina1_img1.png"]
    assert "![](imagenes/pagina1_img1.png)" in markdown
    assert "base64" not in markdown


def test_descargar_indice_desde_marcadores():
    with _abrir_zip(_descargar(_pdf_con_imagenes(marcadores=True))) as zf:
        markdown = zf.read("doc.md").decode()
    assert markdown.startswith("## Índice\n\n- [Informe Anual](#informe-anual)\n  - [Introduccion](#introduccion)\n")


def test_descargar_indice_desde_titulos():
    with _abrir_zip(_descargar(_pdf_con_imagenes())) as zf:
        markdown = zf.read("doc.md").decode()
    assert markdown.startswith("## Índice\n\n- [Informe Anual](#informe-anual)\n")
    assert "- [Introduccion](#introduccion)" in markdown


def test_descargar_archivo_de_texto_es_rechazado():
    r = _descargar(b"hola mundo", "notas.txt", "text/plain")
    assert r.status_code == 400
    assert "no es un PDF" in r.json()["detail"]


def test_descargar_pdf_solo_con_imagen_es_rechazado():
    doc = pymupdf.open()
    pix = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 300, 200), 0)
    doc.new_page().insert_image(pymupdf.Rect(72, 72, 372, 272), pixmap=pix)
    r = _descargar(doc.tobytes())
    assert r.status_code == 422


def test_descarga_no_deja_archivos():
    antes = set(os.listdir(tempfile.gettempdir())), set(os.listdir("."))
    assert _descargar(_pdf_con_imagenes()).status_code == 200
    despues = set(os.listdir(tempfile.gettempdir())), set(os.listdir("."))
    assert despues == antes


def _pdf_con_indice_y_codigo() -> bytes:
    doc = pymupdf.open()
    p = doc.new_page()
    p.insert_text((72, 80), "Indice", fontsize=18)
    y = 110
    for titulo, pagina in [("1. Introduccion", 2), ("2. Instalacion", 2)]:
        p.insert_text((72, y), f"{titulo} {'.' * 60} {pagina}", fontsize=11)
        y += 18
    q = doc.new_page()
    q.insert_text((72, 80), "Instalacion", fontsize=18)
    q.insert_text((72, 110), "Para instalar ejecute el siguiente comando en la terminal:", fontsize=11)
    y = 140
    for linea in ["def hola(nombre):", "    return nombre", "print(hola('mundo'))"]:
        q.insert_text((90, y), linea, fontsize=10, fontname="cour")
        y += 14
    q.insert_text((72, y + 20), "Y ahora los comandos con fuente normal:", fontsize=11)
    y += 40
    for linea in ["pip install fastapi", "fastapi dev app/main.py"]:
        q.insert_text((90, y), linea, fontsize=10)
        y += 14
    q.insert_text((72, y + 20), "Fin del capitulo con texto normal para cerrar.", fontsize=11)
    return doc.tobytes()


def _markdown_descargado(contenido: bytes) -> str:
    with _abrir_zip(_descargar(contenido)) as zf:
        return zf.read("doc.md").decode()


def test_descargar_quita_el_indice_del_pdf():
    markdown = _markdown_descargado(_pdf_con_indice_y_codigo())
    assert markdown.count("Índice") + markdown.count("Indice") == 1
    assert "....." not in markdown
    assert markdown.startswith("## Índice\n\n- [Instalacion](#instalacion)\n")


def test_descargar_codigo_monoespaciado_en_bloque():
    markdown = _markdown_descargado(_pdf_con_indice_y_codigo())
    assert "```\ndef hola(nombre):" in markdown


def test_descargar_comandos_en_fuente_normal_en_bloque():
    markdown = _markdown_descargado(_pdf_con_indice_y_codigo())
    assert "```\npip install fastapi\nfastapi dev app/main.py\n```" in markdown
    assert "Fin del capitulo con texto normal para cerrar." in markdown

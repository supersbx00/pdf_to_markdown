import base64
import io
import re
import zipfile
from pathlib import Path

LIMITE_IMAGEN = 0.05
COMANDOS = {
    "pip", "pip3", "python", "python3", "git", "npm", "npx", "yarn", "node", "docker", "docker-compose",
    "cd", "ls", "mkdir", "rm", "cp", "mv", "sudo", "apt", "apt-get", "curl", "wget", "chmod", "cat",
    "echo", "export", "source", "uvicorn", "fastapi", "pytest", "brew", "ssh", "tar",
}
INICIOS_CODIGO = (
    "$ ", "def ", "class ", "import ", "function ", "const ", "let ", "var ", "return",
    "if ", "if(", "for ", "for(", "while ", "while(", "print(", "console.",
)
TITULO_INDICE = re.compile(r"índice|indice|contenidos?|tabla de contenidos?", re.IGNORECASE)


def to_conversion_response(archivo: str, paginas: int, markdown: str) -> dict:
    return {"archivo": archivo, "paginas": paginas, "markdown": markdown}


def extraer_imagenes(chunk: dict, n: int, ancho: float, alto: float) -> tuple[list, dict[str, bytes]]:
    texto, reemplazos, imagenes = chunk["text"], [], {}
    cajas = sorted((b for b in chunk["page_boxes"] if b["class"] == "picture"), key=lambda b: b["pos"][0])
    for caja in cajas:
        x0, y0, x1, y1 = caja["bbox"]
        inicio, fin = caja["pos"]
        datos = re.search(r"base64,([A-Za-z0-9+/=]+)", texto[inicio:fin])
        if x1 - x0 < ancho * LIMITE_IMAGEN or y1 - y0 < alto * LIMITE_IMAGEN or not datos:
            reemplazos.append((inicio, fin, "\n"))
            continue
        ruta = f"imagenes/pagina{n}_img{len(imagenes) + 1}.png"
        imagenes[ruta] = base64.b64decode(datos.group(1))
        reemplazos.append((inicio, fin, f"\n![]({ruta})\n\n"))
    return reemplazos, imagenes


def _es_codigo(linea: str) -> bool:
    return (
        (linea.split() or [""])[0] in COMANDOS
        or linea.startswith(INICIOS_CODIGO)
        or re.match(r"from \S+ import ", linea) is not None
        or linea.endswith(("{", "}", ";", "):"))
    )


def marcar_codigo(chunk: dict, lineas: dict[int, list[str]]) -> list:
    reemplazos = []
    for caja in (b for b in chunk["page_boxes"] if b["class"] == "text"):
        inicio, fin = caja["pos"]
        lineas_caja = lineas.get(caja["index"])
        if not lineas_caja or chunk["text"][inicio:fin].lstrip().startswith("```"):
            continue
        if all(_es_codigo(linea) for linea in lineas_caja):
            reemplazos.append((inicio, fin, "```\n" + "\n".join(lineas_caja) + "\n```\n\n"))
    return reemplazos


def armar_markdown(
    chunks: list[dict], tamanos: list[tuple[float, float]], lineas: list[dict[int, list[str]]]
) -> tuple[str, dict[str, bytes]]:
    paginas, imagenes = [], {}
    for n, (chunk, (ancho, alto), lineas_pagina) in enumerate(zip(chunks, tamanos, lineas), start=1):
        reemplazos, imagenes_pagina = extraer_imagenes(chunk, n, ancho, alto)
        imagenes.update(imagenes_pagina)
        texto = chunk["text"]
        for inicio, fin, nuevo in sorted(reemplazos + marcar_codigo(chunk, lineas_pagina), reverse=True):
            texto = texto[:inicio] + nuevo + texto[fin:]
        paginas.append(texto)
    return "\n".join(paginas), imagenes


def _titulos(markdown: str) -> list[tuple[int, str, int]]:
    titulos, en_codigo = [], False
    for i, linea in enumerate(markdown.splitlines()):
        if linea.startswith("```"):
            en_codigo = not en_codigo
        elif not en_codigo and (m := re.match(r"(#{1,6}) (.+)$", linea)):
            titulos.append((len(m[1]), m[2].strip(), i))
    return titulos


def _es_titulo_indice(titulo: str) -> bool:
    return TITULO_INDICE.fullmatch(titulo.strip(" *")) is not None


def quitar_indice_pdf(markdown: str, toc: list) -> tuple[str, list]:
    lineas = markdown.splitlines()
    titulos = _titulos(markdown)
    borrar = set()
    for k, (_, titulo, i) in enumerate(titulos):
        if _es_titulo_indice(titulo):
            fin = titulos[k + 1][2] if k + 1 < len(titulos) else len(lineas)
            borrar.update(range(i, fin))
    lineas = [l for i, l in enumerate(lineas) if i not in borrar and not re.search(r"\.{4,}\s*\d+\s*$", l)]
    return "\n".join(lineas), [e for e in toc if not _es_titulo_indice(e[1])]


def _slug(titulo: str) -> str:
    return re.sub(r"[^\w\- ]", "", titulo.strip().lower()).replace(" ", "-")


def armar_indice(markdown: str, toc: list) -> str:
    if toc:
        entradas = [(nivel, titulo) for nivel, titulo, _ in toc]
    else:
        entradas = [(nivel, titulo) for nivel, titulo, _ in _titulos(markdown)]
    if not entradas:
        return markdown
    lineas = [f"{'  ' * (nivel - 1)}- [{titulo.strip()}](#{_slug(titulo)})" for nivel, titulo in entradas]
    return "## Índice\n\n" + "\n".join(lineas) + "\n\n" + markdown


def to_zip(nombre: str, markdown: str, imagenes: dict[str, bytes]) -> tuple[str, bytes]:
    base = Path(nombre or "").stem or "documento"
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"{base}.md", markdown)
        for ruta, datos in imagenes.items():
            zf.writestr(ruta, datos)
    return f"{base}.zip", buffer.getvalue()

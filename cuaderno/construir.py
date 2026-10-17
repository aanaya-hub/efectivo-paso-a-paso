#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
construir.py — convierte `cuaderno/fuente.py` en el notebook ejecutado.

La fuente está en formato «percent» (celdas separadas por `# %%`), que es
texto plano y se revisa en un diff como cualquier otro archivo. Este guion
la convierte a `demo_efectivo.ipynb` en la raíz del proyecto y lo ejecuta
de arriba abajo, para que el notebook que lee el prospecto traiga salidas y
gráficas y no un cuaderno vacío.

    python3 cuaderno/construir.py

Sale con código 1 si alguna celda falla.
"""

from __future__ import annotations

import os
import platform
import sys
import tempfile
from pathlib import Path

import nbformat
from nbclient import NotebookClient

RAIZ = Path(__file__).resolve().parent.parent
FUENTE = Path(__file__).resolve().parent / "fuente.py"
DESTINO = RAIZ / "demo_efectivo.ipynb"

# matplotlib avisa si su carpeta de caché no se puede escribir, y ese aviso
# acabaría dentro del cuaderno publicado. Se le da una carpeta temporal.
os.environ.setdefault("MPLCONFIGDIR", tempfile.mkdtemp(prefix="matplotlib-"))


def partir_celdas(texto: str) -> list[tuple[str, list[str]]]:
    """Parte la fuente en celdas según los separadores `# %%`."""
    celdas: list[tuple[str, list[str]]] = []
    tipo, bufer = None, []
    for linea in texto.splitlines():
        if linea.startswith("# %%"):
            if tipo is not None:
                celdas.append((tipo, bufer))
            tipo = "markdown" if "[markdown]" in linea else "code"
            bufer = []
        else:
            bufer.append(linea)
    if tipo is not None:
        celdas.append((tipo, bufer))
    return celdas


def texto_markdown(lineas: list[str]) -> str:
    """Quita el `# ` con el que se marcan las líneas de una celda de texto."""
    salida = []
    for linea in lineas:
        if linea == "#":
            salida.append("")
        elif linea.startswith("# "):
            salida.append(linea[2:])
        else:
            salida.append(linea)
    return "\n".join(salida).strip("\n")


def texto_codigo(lineas: list[str]) -> str:
    """Quita los renglones vacíos de los extremos y conserva el código tal cual."""
    while lineas and not lineas[0].strip():
        lineas.pop(0)
    while lineas and not lineas[-1].strip():
        lineas.pop()
    return "\n".join(lineas)


def main() -> int:
    """Convierte, ejecuta y reporta."""
    celdas = partir_celdas(FUENTE.read_text(encoding="utf-8"))
    notebook = nbformat.v4.new_notebook()
    for tipo, lineas in celdas:
        if tipo == "markdown":
            notebook.cells.append(nbformat.v4.new_markdown_cell(
                texto_markdown(lineas)))
        else:
            notebook.cells.append(nbformat.v4.new_code_cell(texto_codigo(lineas)))

    notebook.metadata["kernelspec"] = {
        "display_name": "Python 3", "language": "python", "name": "python3"}
    notebook.metadata["language_info"] = {
        "name": "python", "version": platform.python_version()}

    ejecutor = NotebookClient(notebook, timeout=600, kernel_name="python3",
                              resources={"metadata": {"path": str(RAIZ)}})
    ejecutor.execute()

    errores = [(i, salida)
               for i, celda in enumerate(notebook.cells)
               for salida in celda.get("outputs", [])
               if salida.get("output_type") == "error"]
    nbformat.write(notebook, DESTINO)

    codigo = sum(1 for c in notebook.cells if c.cell_type == "code")
    texto = len(notebook.cells) - codigo
    print(f"{DESTINO.name}: {len(notebook.cells)} celdas "
          f"({codigo} de código, {texto} de texto)")
    if errores:
        for indice, salida in errores:
            print(f"  celda {indice}: {salida.get('ename')}: "
                  f"{salida.get('evalue')}")
        return 1
    print("  ejecutado sin errores")
    return 0


if __name__ == "__main__":
    sys.exit(main())

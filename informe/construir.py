#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
construir.py — arma el informe en PDF a partir de `informe.md`.

    python3 informe/construir.py

Hace dos pasos: convierte el Markdown a HTML con pandoc y lo imprime a PDF con
Chromium en modo headless. Deja `informe.html` (para revisarlo en el navegador)
y `informe.pdf` (el entregable). Sale con código 1 si falta una figura o si
alguna herramienta falla.

Se usa Chromium y no WeasyPrint porque la versión instalada de este último no es
compatible con la de `pydyf` que trae el sistema.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
FUENTE = AQUI / "informe.md"
ESTILO = AQUI / "estilo.css"
HTML = AQUI / "informe.html"
PDF = AQUI / "informe.pdf"
FIGURAS = AQUI / "figuras"

PLANTILLA = """<!DOCTYPE html>
<html lang="es-MX">
<head>
<meta charset="utf-8">
<title>Dónde se está deteniendo el dinero — informe de hallazgos</title>
<meta name="author" content="Gato 8 Analítica de Datos · Adan Anaya">
<style>
{css}
</style>
</head>
<body>
{cuerpo}
</body>
</html>
"""


def revisar_figuras(cuerpo: str) -> list[str]:
    """Devuelve las figuras que el Markdown menciona y comprueba que existan."""
    faltantes = []
    for linea in cuerpo.splitlines():
        if "](figuras/" not in linea:
            continue
        ruta = linea.split("](figuras/", 1)[1].split(")", 1)[0]
        if not (FIGURAS / ruta).is_file():
            faltantes.append(ruta)
    return faltantes


def main() -> int:
    """Convierte, envuelve y compone el PDF."""
    if not FUENTE.is_file():
        print(f"falta {FUENTE}")
        return 1

    markdown = FUENTE.read_text(encoding="utf-8")
    faltantes = revisar_figuras(markdown)
    if faltantes:
        for ruta in faltantes:
            print(f"  falta la figura: figuras/{ruta}")
        return 1

    conversion = subprocess.run(
        ["pandoc", str(FUENTE), "--from=markdown", "--to=html5", "--wrap=none"],
        capture_output=True, text=True, check=False)
    if conversion.returncode != 0:
        print(conversion.stderr)
        return 1

    html = PLANTILLA.format(css=ESTILO.read_text(encoding="utf-8"),
                            cuerpo=conversion.stdout)
    HTML.write_text(html, encoding="utf-8")

    compuesto = subprocess.run(
        ["chromium", "--headless", "--no-sandbox", "--disable-gpu",
         "--no-pdf-header-footer", f"--print-to-pdf={PDF}", str(HTML)],
        capture_output=True, text=True, check=False)
    if compuesto.returncode != 0 or not PDF.is_file():
        print(compuesto.stderr[-2000:])
        return 1

    kb = PDF.stat().st_size / 1024
    print(f"{PDF.name}: {kb:.0f} KB · fuente {FUENTE.name} · "
          f"{len(markdown.splitlines())} renglones")
    return 0


if __name__ == "__main__":
    sys.exit(main())

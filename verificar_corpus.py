#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verificar_corpus.py — control de calidad del generador.

No forma parte de la narrativa del demo: es la comprobación de que el corpus
sintético (a) contiene los ocho defectos que promete el brief y (b) se puede
limpiar hasta cuadrar **al centavo** contra el reporte del dueño.

    python3 verificar_corpus.py

Si algo no cuadra, sale con código 1.
"""

from __future__ import annotations

import csv
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

RUTA = Path(__file__).resolve().parent / "datos" / "recibido"
IVA = 0.16
FALLAS: list[str] = []


def leer(nombre: str) -> list[dict]:
    """Lee un CSV del corpus como lista de diccionarios."""
    with (RUTA / nombre).open(encoding="utf-8-sig") as archivo:
        return list(csv.DictReader(archivo))


def revisar(condicion: bool, mensaje: str) -> None:
    """Registra una comprobación y avisa si falla."""
    print(("  ok   " if condicion else "  FALLA ") + mensaje)
    if not condicion:
        FALLAS.append(mensaje)


def a_fecha(texto: str) -> tuple[date | None, str]:
    """Interpreta la fecha del archivo y dice cómo la interpretó."""
    if "-" in texto:
        anio, mes, dia = (int(p) for p in texto.split("-"))
        return date(anio, mes, dia), "iso"
    a, b, anio = (int(p) for p in texto.split("/"))
    if a > 12:                                     # imposible como mes: es dd/mm
        return date(anio, b, a), "dd/mm"
    if b > 12:                                     # imposible como día en mm/dd: es mm/dd
        return date(anio, a, b), "mm/dd"
    return date(anio, b, a), "ambiguo-dd/mm"       # se resuelve más adelante


def main() -> int:
    """Corre todas las comprobaciones del corpus."""
    ventas = leer("ventas_12_meses.csv")
    productos = {p["codigo"]: p for p in leer("productos.csv")}
    clientes = {c["codigo"]: c for c in leer("clientes.csv")}
    notas = leer("notas_credito.csv")
    facturas = {f["folio"]: f for f in leer("facturas.csv")}
    pagos = leer("pagos.csv")
    control = leer("reporte_mensual_ventas.csv")

    print(f"filas de venta: {len(ventas):,}   notas: {len(notas):,}   "
          f"facturas: {len(facturas):,}   pagos: {len(pagos):,}")

    # --- defecto 1 · fechas como texto, mezclando dd/mm y mm/dd -------------
    print("\n[1] fechas como texto")
    formatos = Counter()
    for fila in ventas:
        _, como = a_fecha(fila["fecha"])
        formatos[como] += 1
    print(f"       {dict(formatos)}")

    # --- defecto 2 y 7 · duplicados ----------------------------------------
    print("\n[2/7] duplicados")
    llave = lambda f: (a_fecha(f["fecha"])[0], f["cliente_codigo"], f["producto_codigo"],
                       f["cantidad"], f["precio_unitario"], f["importe"])
    grupos = defaultdict(list)
    for fila in ventas:
        grupos[llave(fila)].append(fila)
    repetidos = {k: v for k, v in grupos.items() if len(v) > 1}
    lotes_repetidos = Counter(f["lote_carga"] for v in repetidos.values()
                              for f in v if f["lote_carga"].endswith(("-B", "-RC")))
    print(f"       grupos con más de una fila: {len(repetidos):,} "
          f"(lotes: {dict(lotes_repetidos)})")
    revisar(len(repetidos) > 0, "hay filas duplicadas por llave de negocio")
    revisar(all(f["lote_carga"].endswith(("-B", "-RC"))
                for v in repetidos.values() for f in v[1:]),
            "todo duplicado viene de una carga marcada -B o -RC")
    limpio = [v[0] for v in grupos.values()]                     # se queda una por grupo
    print(f"       filas después de deduplicar: {len(limpio):,}")

    # --- defecto 4 · precios con y sin IVA ---------------------------------
    print("\n[4] precios con y sin IVA")
    ratio_lote = defaultdict(list)
    for fila in limpio:
        lista = float(productos[fila["producto_codigo"]]["precio_lista_sin_iva"])
        ratio_lote[fila["lote_carga"]].append(float(fila["precio_unitario"]) / lista)
    lotes_sin_iva = set()
    for lote, ratios in sorted(ratio_lote.items()):
        mediana = sorted(ratios)[len(ratios) // 2]
        if mediana < 1.0:                                        # por debajo de lista
            lotes_sin_iva.add(lote)
    print(f"       lotes sin IVA detectados: {sorted(lotes_sin_iva)}")
    revisar(len(lotes_sin_iva) == 3, "se detectaron tres lotes exportados sin IVA")

    # --- defecto 3 · notas de crédito --------------------------------------
    print("\n[3] notas de crédito que no se restaron")
    total_notas = round(sum(float(n["importe_con_iva"]) for n in notas), 2)
    print(f"       {len(notas):,} notas por {total_notas:,.2f} con IVA")
    tasa = [float(n["importe_con_iva"]) / float(n["importe_sin_iva"]) for n in notas]
    print(f"       tasa implícita: {min(tasa):.6f} a {max(tasa):.6f}")
    revisar(all(abs(t - (1 + IVA)) < 0.0005 for t in tasa),
            "la tasa de IVA se comprueba en las notas, no se supone")

    # --- defecto 5 · dos clientes con el mismo nombre ----------------------
    print("\n[5] el mismo cliente con dos códigos")
    por_nombre = defaultdict(list)
    for c in clientes.values():
        por_nombre[c["nombre"]].append(c)
    pares = {n: v for n, v in por_nombre.items() if len(v) > 1}
    for nombre, v in pares.items():
        misma = len({c["rfc"] for c in v}) == 1
        print(f"       {nombre}: {[c['codigo'] for c in v]} · "
              f"{'mismo RFC' if misma else 'RFC distinto'}")
    revisar(len(pares) == 1, "hay exactamente un par de cuentas del mismo negocio")

    # --- defecto 6 · un producto que cambió de nombre ----------------------
    print("\n[6] producto renombrado a mitad del año")
    nombres = defaultdict(set)
    for fila in limpio:
        nombres[fila["producto_codigo"]].add(fila["producto_nombre"])
    cambiados = {c: n for c, n in nombres.items() if len(n) > 1}
    for codigo, conjunto in cambiados.items():
        print(f"       {codigo}: {sorted(conjunto)}")
    revisar(len(cambiados) == 1, "hay exactamente un producto con dos nombres")

    # --- defecto 8 · un pago aplicado a la factura equivocada --------------
    print("\n[8] pago aplicado a la factura equivocada")
    imposibles = [p for p in pagos
                  if p["factura_aplicada"] in facturas
                  and p["fecha_pago"] < facturas[p["factura_aplicada"]]["fecha_emision"]]
    for p in imposibles:
        print(f"       {p['folio_pago']} del {p['fecha_pago']} aplicado a "
              f"{p['factura_aplicada']} emitida el "
              f"{facturas[p['factura_aplicada']]['fecha_emision']} por {p['importe']}")
    revisar(len(imposibles) == 1, "hay exactamente un pago anterior a su factura")

    # --- el cuadre contra el reporte del dueño ----------------------------
    print("\n[cuadre] limpiar y cuadrar contra reporte_mensual_ventas.csv")
    bruto = defaultdict(float)
    ambiguas_resueltas, ambiguas_sueltas = 0, 0
    for fila in limpio:
        fecha, como = a_fecha(fila["fecha"])
        if como == "ambiguo-dd/mm":                    # dd/mm contra mm/dd: hay que
            if fila["folio"] in facturas:              # resolverlo con otra fuente
                fecha = date(*map(int, facturas[fila["folio"]]["fecha_emision"]
                                  .split("-")))
                ambiguas_resueltas += 1
            else:                                      # sin factura: queda como dd/mm
                ambiguas_sueltas += 1
        precio = float(fila["precio_unitario"])
        if fila["lote_carga"] in lotes_sin_iva:        # se recupera la base con IVA
            precio = round(precio * (1 + IVA), 2)
        importe = round(float(fila["cantidad"]) * precio, 2)
        bruto[f"{fecha.year}-{fecha.month:02d}"] += importe
    print(f"       fechas ambiguas resueltas con el sistema: {ambiguas_resueltas:,} · "
          f"sin contraparte: {ambiguas_sueltas:,}")
    for nota in notas:
        anio, mes, _ = (int(p) for p in nota["fecha_nota"].split("-"))
        bruto[f"{anio}-{mes:02d}"] -= float(nota["importe_con_iva"])

    diferencias = []
    for fila in control:
        mio = round(bruto[fila["mes"]], 2)
        suyo = float(fila["ventas_netas_con_iva"])
        if abs(mio - suyo) > 0.005:
            diferencias.append((fila["mes"], mio, suyo, round(mio - suyo, 2)))
    if diferencias:
        for mes, mio, suyo, dif in diferencias:
            print(f"       {mes}: mío {mio:,.2f} · suyo {suyo:,.2f} · dif {dif:,.2f}")
    revisar(not diferencias,
            f"los doce meses cuadran al centavo "
            f"(total {sum(float(f['ventas_netas_con_iva']) for f in control):,.2f})")

    print("\n" + ("TODO EN ORDEN" if not FALLAS else f"{len(FALLAS)} FALLAS"))
    return 1 if FALLAS else 0


if __name__ == "__main__":
    sys.exit(main())

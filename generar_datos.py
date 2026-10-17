#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generar_datos.py — corpus sintético del demo «cómo trabajo, paso a paso».

No es un guion de trabajo de cliente: es el generador del caso ficticio.
Escribe en `datos/recibido/` los archivos que «mandó» la empresa, con sus
ocho defectos sembrados, más el reporte mensual que el dueño usa como total
de control.

    python3 generar_datos.py

La semilla es fija: dos corridas producen los mismos números. Todo dato de
persona o empresa es inventado; ningún RFC corresponde a un contribuyente.
"""

from __future__ import annotations

import csv
import math
import random
from datetime import date, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# 0 · Parámetros del caso
# ---------------------------------------------------------------------------

SEMILLA = 20261016                         # semilla fija: reproducible
IVA = 0.16                                 # tasa de IVA vigente en México
CORTE = date(2026, 9, 30)                  # último día de la ventana de datos
FECHA_CAMBIO_SISTEMA = date(2026, 4, 1)    # cambio de rutina de exportación
FECHA_CORTE_INVENTARIO = date(2026, 6, 30) # corte del inventario que mandaron
INICIO_CARTERA = date(2026, 4, 1)          # el sistema solo da 6 meses de facturas

MESES = [                                   # ventana: oct-2025 a sep-2026
    (2025, 10), (2025, 11), (2025, 12),
    (2026, 1), (2026, 2), (2026, 3), (2026, 4), (2026, 5), (2026, 6),
    (2026, 7), (2026, 8), (2026, 9),
]

ESTACIONALIDAD = {                          # la temporada de abarrotes, mes a mes
    10: 1.00, 11: 1.05, 12: 1.22, 1: 0.84, 2: 0.92, 3: 1.00,
    4: 1.02, 5: 1.05, 6: 0.98, 7: 0.96, 8: 0.99, 9: 0.97,
}

FACTURAS_POR_MES = 87                       # documentos base en un mes normal
MES_DUPLICADO = (2026, 6)                   # el mes que se cargó dos veces
LOTES_SIN_IVA = {(2026, 5), (2026, 6), (2026, 7)}   # se exportaron sin IVA
PROB_REMISION = 0.03                        # documentos sin CFDI (nota de venta)
PROB_MOROSO = 0.26                          # clientes que se atoran de verdad
PROB_PAGO_PARCIAL = 0.24                    # pagos en abonos, lo normal en mayoreo
ATRASO_EXTRA_V03 = 18                       # días extra del vendedor más lento
PROB_FECHA_MMDD = 0.12                      # filas con fecha escrita mm/dd

MARCAS = [                                  # marcas inventadas del catálogo
    "Cerro Prieto", "Doña Filo", "Río Claro", "Monte Alto", "La Troje",
    "Sol de Mayo", "Agua Nueva", "El Nopalito", "Rancho Viejo", "Piedra Blanca",
]

TIPOS_NEGOCIO = [
    "Abarrotes", "Tienda", "Miscelánea", "Depósito", "Bodega", "Mini súper",
    "Autoservicio", "Comercializadora", "Fonda", "Cocina económica",
]

NOMBRES_BASE = [                            # la segunda mitad del nombre del cliente
    "El Roble", "La Esquina", "San Judas", "Las Palmas", "El Mirador",
    "La Loma", "Los Pinos", "El Crucero", "La Estación", "Santa Rita",
    "El Faro", "Las Flores", "La Cascada", "El Puente", "Los Arcos",
    "La Presa", "El Cerrito", "Las Ánimas", "San Pedro", "La Cima",
    "El Chorrito", "Los Naranjos", "La Viga", "El Refugio", "La Gloria",
    "Los Sauces", "El Salto", "La Aurora", "San Isidro", "Las Trojes",
    "El Ancla", "La Calera", "Los Fresnos", "El Trapiche", "La Noria",
    "San Blas", "Las Juntas", "El Pueblito", "La Yesca", "Los Tarascos",
]

CIUDADES = [
    "Guadalajara", "Zapopan", "Tlaquepaque", "Tonalá", "Tlajomulco",
    "El Salto", "Juanacatlán", "Chapala", "Ixtlahuacán", "Zapotlanejo",
]

VENDEDORES = [
    {"codigo": "V-01", "nombre": "Ramiro Espinoza", "peso": 0.40},
    {"codigo": "V-02", "nombre": "Lucía Barragán", "peso": 0.35},
    {"codigo": "V-03", "nombre": "Óscar Medina", "peso": 0.25},
]

# tipo, categoría, unidad, presentaciones, costo de la presentación menor
TIPOS_PRODUCTO = [
    ("Aceite vegetal", "Abarrotes", "botella", ["900 ml", "1 L", "3 L", "5 L", "20 L"], 34.0),
    ("Arroz", "Abarrotes", "bolsa", ["1 kg", "2 kg", "5 kg", "10 kg", "25 kg"], 22.0),
    ("Azúcar estándar", "Abarrotes", "bolsa", ["1 kg", "2 kg", "5 kg", "10 kg", "25 kg"], 24.0),
    ("Frijol negro", "Abarrotes", "bolsa", ["1 kg", "2 kg", "5 kg", "10 kg", "25 kg"], 26.0),
    ("Lenteja", "Abarrotes", "bolsa", ["500 g", "1 kg", "2 kg", "5 kg", "10 kg"], 18.0),
    ("Pasta para sopa", "Abarrotes", "paquete", ["200 g", "500 g", "1 kg", "3 kg", "5 kg"], 12.0),
    ("Harina de maíz", "Abarrotes", "bolsa", ["1 kg", "2 kg", "5 kg", "10 kg", "20 kg"], 20.0),
    ("Sal de mesa", "Abarrotes", "bolsa", ["1 kg", "2 kg", "5 kg", "10 kg", "25 kg"], 9.0),
    ("Atún en agua", "Abarrotes", "lata", ["140 g", "170 g", "200 g", "300 g", "500 g"], 17.0),
    ("Sardina en tomate", "Abarrotes", "lata", ["155 g", "200 g", "300 g", "400 g", "500 g"], 14.0),
    ("Café molido", "Abarrotes", "paquete", ["250 g", "500 g", "1 kg", "2 kg", "5 kg"], 58.0),
    ("Chocolate en polvo", "Abarrotes", "caja", ["400 g", "800 g", "1 kg", "2 kg", "5 kg"], 44.0),
    ("Galletas Marías", "Abarrotes", "paquete", ["170 g", "350 g", "500 g", "1 kg", "2 kg"], 13.0),
    ("Cereal de maíz", "Abarrotes", "caja", ["250 g", "400 g", "600 g", "1 kg", "2 kg"], 27.0),
    ("Jabón de barra", "Limpieza", "pieza", ["150 g", "200 g", "300 g", "400 g", "500 g"], 9.5),
    ("Detergente en polvo", "Limpieza", "bolsa", ["500 g", "1 kg", "2 kg", "5 kg", "10 kg"], 22.0),
    ("Suavizante de telas", "Limpieza", "botella", ["850 ml", "1 L", "2 L", "3 L", "5 L"], 26.0),
    ("Blanqueador", "Limpieza", "botella", ["950 ml", "1 L", "2 L", "4 L", "10 L"], 18.0),
    ("Limpiador líquido", "Limpieza", "botella", ["900 ml", "1 L", "2 L", "4 L", "10 L"], 21.0),
    ("Jabón líquido para trastes", "Limpieza", "botella", ["500 ml", "750 ml", "1 L", "2 L", "5 L"], 24.0),
    ("Bolsa para basura", "Limpieza", "paquete", ["10 pzas", "20 pzas", "50 pzas", "100 pzas", "200 pzas"], 16.0),
    ("Papel higiénico", "Limpieza", "paquete", ["4 rollos", "12 rollos", "24 rollos", "48 rollos", "96 rollos"], 28.0),
    ("Servilletas", "Limpieza", "paquete", ["100 pzas", "250 pzas", "500 pzas", "1000 pzas", "2000 pzas"], 15.0),
    ("Toallas de papel", "Limpieza", "paquete", ["2 rollos", "4 rollos", "6 rollos", "12 rollos", "24 rollos"], 19.0),
]

FACTOR_PRESENTACION = [1.0, 1.9, 4.6, 9.0, 21.0]   # el costo crece con el tamaño

# a qué presentación le tira cada tipo de cliente (0 = la más chica)
SESGO_MAYOREO = [0.25, 0.55, 1.0, 2.4, 4.2]
SESGO_MENUDEO = [4.0, 2.4, 1.0, 0.45, 0.18]

# importe objetivo de una línea, por tipo de cliente (mediana, sigma del lognormal)
IMPORTE_LINEA = {"Mayoreo": (12000.0, 0.55), "Menudeo": (2600.0, 0.50)}

MOTIVOS_NOTA = [
    "producto dañado en el traslado", "faltante en el pedido",
    "producto caducado", "error de surtido", "precio cobrado distinto al pactado",
]

RUTA = Path(__file__).resolve().parent
RUTA_RECIBIDO = RUTA / "datos" / "recibido"


# ---------------------------------------------------------------------------
# 1 · Utilidades
# ---------------------------------------------------------------------------

def redondear(x: float) -> float:
    """Redondea a dos centavos, como lo hace un sistema de facturación."""
    return round(x + 1e-9, 2)


def precio_con_iva(precio_sin_iva: float) -> float:
    """Pasa un precio de la base sin IVA a la base con IVA, a dos decimales."""
    return redondear(precio_sin_iva * (1 + IVA))


def importe_sin_iva_desde_con_iva(importe_con_iva: float) -> float:
    """Deshace el IVA de un importe ya redondeado. Es la única ruta que se usa."""
    return redondear(importe_con_iva / (1 + IVA))


def dias_del_mes(anio: int, mes: int) -> int:
    """Cuenta los días del mes sin depender de calendarios externos."""
    siguiente = date(anio + (mes == 12), mes % 12 + 1, 1)
    return (siguiente - date(anio, mes, 1)).days


def dia_habil(rng: random.Random, anio: int, mes: int) -> int:
    """Elige un día del mes entre semana, con algo más de peso a media quincena."""
    dias = [d for d in range(1, dias_del_mes(anio, mes) + 1)      # todos los días
            if date(anio, mes, d).weekday() != 6]                 # fuera domingos
    pesos = [1.0 + 0.9 * math.exp(-((d - 15) ** 2) / 60)          # pico a media quincena
             for d in dias]
    return rng.choices(dias, weights=pesos, k=1)[0]


def etiqueta_mes(anio: int, mes: int) -> str:
    """Devuelve el mes en el formato que usa el reporte del dueño."""
    return f"{anio}-{mes:02d}"


def elegir_ponderado(rng: random.Random, elementos: list, pesos: list):
    """Elige un elemento de una lista según sus pesos (una sola vez)."""
    return rng.choices(elementos, weights=pesos, k=1)[0]


def rfc_inventado(rng: random.Random, nombre: str) -> str:
    """Fabrica un RFC con forma verosímil. No corresponde a ningún contribuyente."""
    letras = "".join(c for c in nombre.upper() if c.isalpha())[:3].ljust(3, "X")
    fecha = f"{rng.randint(0, 99):02d}{rng.randint(1, 12):02d}{rng.randint(0, 99):02d}"
    homo = "".join(rng.choice("0123456789ABCDEFGHJKLMNPQRSTUVWXYZ") for _ in range(3))
    return f"{letras}{fecha}{homo}"


# ---------------------------------------------------------------------------
# 2 · Catálogo de productos
# ---------------------------------------------------------------------------

def construir_productos(rng: random.Random) -> list[dict]:
    """Arma los 120 productos con su costo, su precio de lista y su popularidad."""
    productos, codigo = [], 0
    for indice_tipo, (tipo, categoria, unidad, presentaciones, costo_base) in \
            enumerate(TIPOS_PRODUCTO):
        marca = MARCAS[indice_tipo % len(MARCAS)]                    # una marca por tipo
        for i, presentacion in enumerate(presentaciones):
            codigo += 1                                              # consecutivo
            costo = costo_base * FACTOR_PRESENTACION[i] * rng.uniform(0.97, 1.03)
            margen = (rng.uniform(0.20, 0.34) if categoria == "Limpieza"
                      else rng.uniform(0.14, 0.24))                  # el margen del giro
            productos.append({
                "codigo": f"P-{codigo:04d}",
                "nombre": f"{tipo} {marca} {presentacion}",
                "categoria": categoria,
                "unidad": unidad,
                "presentacion": presentacion,
                "indice_presentacion": i,
                "costo": redondear(costo),
                "precio_lista": redondear(costo * (1 + margen)),
                "peso": rng.lognormvariate(0.0, 0.62),               # popularidad
                "prob_devolucion": 0.035,                            # se ajusta abajo
                "nombre_nuevo": None,
            })
    return productos


def sembrar_defectos_de_catalogo(rng: random.Random, productos: list[dict]) -> dict:
    """Marca los productos que cargan un defecto: margen negativo y renombre."""
    populares = sorted(productos, key=lambda p: -p["peso"])          # los que más rotan

    for p in (populares[1], populares[6], populares[11], populares[15]):
        p["precio_lista"] = redondear(p["costo"] * rng.uniform(0.93, 0.98))

    renombrado = populares[2]                                        # el que cambió de nombre
    renombrado["nombre_nuevo"] = renombrado["nombre"] + " (nuevo empaque)"

    devolvedor = populares[4]                                        # el que más se devuelve
    devolvedor["prob_devolucion"] = 0.22
    populares[9]["prob_devolucion"] = 0.10

    return {
        "negativos": [p["codigo"] for p in
                      (populares[1], populares[6], populares[11], populares[15])],
        "renombrado": renombrado["codigo"],
        "devolvedor": devolvedor["codigo"],
    }


# ---------------------------------------------------------------------------
# 3 · Catálogo de clientes
# ---------------------------------------------------------------------------

def construir_clientes(rng: random.Random) -> list[dict]:
    """Arma los 180 clientes y siembra el par con el mismo nombre y dos códigos."""
    combos = [f"{t} {n}" for t in TIPOS_NEGOCIO for n in NOMBRES_BASE]
    nombres = rng.sample(combos, 180)                                # sin repetir

    clientes = []
    for i, nombre in enumerate(nombres):
        tipo = "Mayoreo" if rng.random() < 0.45 else "Menudeo"
        credito = elegir_ponderado(rng, [30, 60, 90], [0.55, 0.30, 0.15]) \
            if tipo == "Mayoreo" else elegir_ponderado(rng, [30, 60], [0.85, 0.15])
        clientes.append({
            "codigo": f"C-{i + 1:04d}",
            "nombre": nombre,
            "rfc": rfc_inventado(rng, nombre),
            "tipo": tipo,
            "ciudad": elegir_ponderado(rng, CIUDADES,
                                       [30, 22, 12, 9, 8, 6, 4, 4, 3, 2]),
            "fecha_alta": date(rng.randint(2015, 2025), rng.randint(1, 12), 1),
            "credito_dias": credito,
            "vendedor": elegir_ponderado(rng, VENDEDORES,
                                         [v["peso"] for v in VENDEDORES])["codigo"],
            "moroso": rng.random() < PROB_MOROSO,                    # nunca paga a tiempo
            "peso": rng.lognormvariate(0.0, 0.95),                   # cuánto compra
        })

    # el par con el mismo nombre: mismo negocio, dos cuentas en el sistema
    orden = sorted(clientes, key=lambda c: -c["peso"])
    for c in (orden[3], orden[11]):
        c["nombre"] = "Depósito La Calandria"
        c["ciudad"] = "Zapopan"
        c["rfc"] = "DEC180607QX3"                                    # el mismo contribuyente
        c["peso"] *= 1.15                                            # y volumen real
        c["tipo"] = "Mayoreo"
    orden[3]["credito_dias"] = 60
    orden[11]["credito_dias"] = 90                                   # condiciones distintas
    orden[11]["vendedor"] = "V-03"                                   # y otro vendedor

    return clientes


# ---------------------------------------------------------------------------
# 4 · Ventas verdaderas (antes de ensuciarlas)
# ---------------------------------------------------------------------------

def generar_ventas(rng: random.Random, clientes: list[dict],
                   productos: list[dict]) -> list[dict]:
    """Genera las líneas de venta limpias de los doce meses."""
    pesos_cliente = [c["peso"] for c in clientes]                     # Pareto de compra
    por_tipo = {
        "Mayoreo": ([p for p in productos if p["indice_presentacion"] >= 2],
                    [p["peso"] * SESGO_MAYOREO[p["indice_presentacion"]]
                     for p in productos if p["indice_presentacion"] >= 2]),
        "Menudeo": ([p for p in productos if p["indice_presentacion"] <= 3],
                    [p["peso"] * SESGO_MENUDEO[p["indice_presentacion"]]
                     for p in productos if p["indice_presentacion"] <= 3]),
    }
    lineas, firmas = [], set()                                       # firmas: evita choques

    for anio, mes in MESES:
        n_documentos = int(round(FACTURAS_POR_MES * ESTACIONALIDAD[mes]
                                 * rng.uniform(0.94, 1.06)))
        for k in range(n_documentos):
            cliente = elegir_ponderado(rng, clientes, pesos_cliente)
            fecha = date(anio, mes, dia_habil(rng, anio, mes))
            es_remision = rng.random() < PROB_REMISION                  # sin CFDI
            folio = f"{'NV' if es_remision else 'F'}-{anio}-{mes:02d}-{k + 1:04d}"
            lineas_doc = elegir_ponderado(rng, [1, 2, 3, 4, 5, 6, 8, 10, 12, 14],
                                          [6, 14, 18, 18, 14, 10, 8, 4, 1, 1])
            catalogo, pesos_prod = por_tipo[cliente["tipo"]]            # sesgo por tipo
            usados = set()                                             # un producto por doc

            for _ in range(lineas_doc):
                for _intento in range(12):
                    producto = elegir_ponderado(rng, catalogo, pesos_prod)
                    if producto["codigo"] in usados:
                        continue
                    mediana, sigma = IMPORTE_LINEA[cliente["tipo"]]
                    objetivo = rng.lognormvariate(math.log(mediana), sigma)
                    descuento = (rng.uniform(0.04, 0.12) if cliente["tipo"] == "Mayoreo"
                                 else rng.uniform(0.0, 0.04))
                    p_sin = redondear(producto["precio_lista"] * (1 - descuento))
                    cantidad = max(1, min(250, round(objetivo / p_sin)))
                    firma = (fecha, cliente["codigo"], producto["codigo"],
                             cantidad, p_sin)
                    if firma in firmas:                                # choque real: redibuja
                        continue
                    firmas.add(firma)
                    usados.add(producto["codigo"])
                    i_con = redondear(cantidad * precio_con_iva(p_sin))
                    nombre = (producto["nombre_nuevo"]
                              if producto["nombre_nuevo"] and
                              fecha >= FECHA_CAMBIO_SISTEMA else producto["nombre"])
                    lineas.append({
                        "fecha": fecha,
                        "folio": folio,
                        "cliente": cliente,
                        "producto": producto,
                        "producto_nombre": nombre,
                        "cantidad": cantidad,
                        "precio_sin_iva": p_sin,
                        "importe_con_iva": i_con,
                        "costo_total": redondear(cantidad * producto["costo"]),
                        "es_remision": es_remision,
                    })
                    break

    lineas.sort(key=lambda l: (l["fecha"], l["folio"]))
    return lineas


def generar_notas(rng: random.Random, lineas: list[dict]) -> list[dict]:
    """Emite las notas de crédito por devoluciones, con su fecha propia."""
    notas = []
    for linea in lineas:
        if rng.random() >= linea["producto"]["prob_devolucion"]:
            continue
        fecha_nota = linea["fecha"] + timedelta(days=rng.randint(3, 28))
        if fecha_nota > CORTE:                                       # fuera de la ventana
            continue
        notas.append({
            "folio_nota": f"NC-{fecha_nota.year}-{len(notas) + 1:04d}",
            "fecha_nota": fecha_nota,
            "cliente": linea["cliente"],
            "folio_factura": linea["folio"],
            "producto": linea["producto"],
            "cantidad": linea["cantidad"],
            "importe_con_iva": linea["importe_con_iva"],
            "motivo": rng.choice(MOTIVOS_NOTA),
        })
    return notas


# ---------------------------------------------------------------------------
# 5 · Cartera: facturas, pagos y el pago mal aplicado
# ---------------------------------------------------------------------------

def generar_cartera(rng: random.Random, lineas: list[dict]) -> tuple[list, list]:
    """Arma facturas y pagos de los últimos seis meses, con un pago mal aplicado."""
    facturas = {}
    for linea in lineas:
        if linea["es_remision"] or linea["fecha"] < INICIO_CARTERA:
            continue                                                 # sin CFDI o fuera
        f = facturas.setdefault(linea["folio"], {
            "folio": linea["folio"],
            "cliente": linea["cliente"],
            "fecha_emision": linea["fecha"],
            "importe": 0.0,
        })
        f["importe"] = redondear(f["importe"] + linea["importe_con_iva"])
    for f in facturas.values():
        f["fecha_vencimiento"] = f["fecha_emision"] + timedelta(
            days=f["cliente"]["credito_dias"])

    pagos = []                                                       # pagos armados
    for folio, f in sorted(facturas.items()):
        vendedor = f["cliente"]["vendedor"]
        es_moroso = f["cliente"]["moroso"]                           # el cliente se atora
        atraso = (rng.gauss(18, 20)                                   # atraso típico
                  + (rng.gauss(150, 55) if es_moroso else 0)          # el que no paga
                  + (ATRASO_EXTRA_V03 if vendedor == "V-03" else 0))
        fecha_completa = f["fecha_emision"] + timedelta(
            days=max(1, int(f["cliente"]["credito_dias"] * 0.9 + atraso)))

        parcial = rng.random() < PROB_PAGO_PARCIAL                    # paga en abonos
        pagado = 0.0
        if fecha_completa <= CORTE:                                   # ya liquidó
            abonos = [(fecha_completa, f["importe"])]
            if parcial:                                               # primer abono antes
                primera = f["fecha_emision"] + timedelta(days=rng.randint(8, 30))
                if primera < fecha_completa:
                    monto = redondear(f["importe"] * rng.uniform(0.3, 0.7))
                    abonos = [(primera, monto),
                              (fecha_completa, redondear(f["importe"] - monto))]
            for fecha_pago, monto in abonos:
                if fecha_pago > CORTE or monto <= 0:
                    continue
                pagos.append({"cliente": f["cliente"], "factura": folio,
                              "fecha_pago": fecha_pago, "importe": redondear(monto)})
                pagado = redondear(pagado + monto)
        elif parcial:                                                 # abonó y quedó saldo
            primera = f["fecha_emision"] + timedelta(days=rng.randint(8, 30))
            if primera <= CORTE:
                monto = redondear(f["importe"] * rng.uniform(0.2, 0.6))
                pagos.append({"cliente": f["cliente"], "factura": folio,
                              "fecha_pago": primera, "importe": monto})
                pagado = monto
        f["pagado"] = pagado
        f["saldo"] = redondear(f["importe"] - pagado)

    return list(facturas.values()), pagos


def aplicar_pago_equivocado(rng: random.Random, facturas: dict, pagos: list) -> dict:
    """Aplica un pago grande a la factura equivocada del mismo cliente."""
    abiertas = [f for f in facturas.values() if f["saldo"] > 0]       # cartera viva
    antiguas = [f for f in abiertas                                   # las vencidas de
                if (CORTE - f["fecha_vencimiento"]).days > 90          # más de 90 días
                and f["importe"] >= 60000]                            # y de monto alto
    if not antiguas:                                                  # sin tope de atraso
        antiguas = [f for f in abiertas if f["importe"] >= 40000]
    if not antiguas:
        return {}

    for victima in sorted(antiguas, key=lambda f: -f["importe"]):     # de mayor a menor
        fecha_pago = victima["fecha_emision"] + timedelta(days=20)    # cuándo pagó
        candidatas = [f for f in facturas.values()                    # facturas del mismo
                      if f is not victima                             # cliente, posteriores
                      and f["cliente"]["codigo"] == victima["cliente"]["codigo"]
                      and f["importe"] >= victima["importe"]          # y que alcancen
                      and f["fecha_emision"] > fecha_pago + timedelta(days=20)]
        if not candidatas:
            continue
        destino = min(candidatas,                                    # la más cercana en el
                      key=lambda f: (f["fecha_emision"]              # tiempo: un pago
                                     - fecha_pago).days)             # muy lejano se nota
        if (destino["fecha_emision"] - fecha_pago).days > 100:        # demasiado lejos:
            continue                                                 # busca otra víctima

        pagos[:] = [p for p in pagos if p["factura"] != destino["folio"]]
        pagos.append({"cliente": destino["cliente"], "factura": destino["folio"],
                      "fecha_pago": fecha_pago, "importe": victima["importe"]})
        destino["pagado"] = victima["importe"]                        # el abono cayó aquí
        destino["saldo"] = redondear(destino["importe"] - destino["pagado"])
        return {"victima": victima["folio"], "destino": destino["folio"],
                "importe": victima["importe"], "fecha_pago": fecha_pago,
                "emision_destino": destino["fecha_emision"]}
    return {}


# ---------------------------------------------------------------------------
# 6 · Degradación: lo que llegó, con sus defectos
# ---------------------------------------------------------------------------

def formatear_fecha(rng: random.Random, fecha: date, corromper: bool) -> str:
    """Escribe la fecha como texto. Con `corromper`, mezcla dd/mm y mm/dd."""
    if not corromper:
        return fecha.isoformat()
    if rng.random() < PROB_FECHA_MMDD:                               # formato ajeno
        return f"{fecha.month:02d}/{fecha.day:02d}/{fecha.year}"
    return f"{fecha.day:02d}/{fecha.month:02d}/{fecha.year}"


def ensuciar_ventas(rng: random.Random, lineas: list[dict]) -> list[dict]:
    """Devuelve las filas del archivo de ventas, con los defectos sembrados."""
    filas = []
    for linea in lineas:
        lote = f"L-{linea['fecha'].year}-{linea['fecha'].month:02d}"  # carga del mes
        sin_iva = (linea["fecha"].year, linea["fecha"].month) in LOTES_SIN_IVA
        precio = (linea["precio_sin_iva"] if sin_iva
                  else precio_con_iva(linea["precio_sin_iva"]))
        importe = (redondear(linea["cantidad"] * linea["precio_sin_iva"]) if sin_iva
                   else linea["importe_con_iva"])
        filas.append({
            "_orden": (linea["fecha"], linea["folio"], linea["producto"]["codigo"]),
            "fecha": formatear_fecha(rng, linea["fecha"],
                                     linea["fecha"] >= FECHA_CAMBIO_SISTEMA
                                     and not linea["es_remision"]),
            "folio": linea["folio"],
            "lote_carga": lote,
            "cliente_codigo": linea["cliente"]["codigo"],
            "cliente_nombre": linea["cliente"]["nombre"],
            "producto_codigo": linea["producto"]["codigo"],
            "producto_nombre": linea["producto_nombre"],
            "cantidad": linea["cantidad"],
            "unidad": linea["producto"]["unidad"],
            "precio_unitario": precio,
            "importe": importe,
            "vendedor": linea["cliente"]["vendedor"],
        })

    # defecto 7 · el mes que se cargó dos veces (folios nuevos, carga distinta)
    anio, mes = MES_DUPLICADO
    for fila in list(filas):
        if fila["lote_carga"] != f"L-{anio}-{mes:02d}":
            continue
        copia = dict(fila)
        copia["_orden"] = (fila["_orden"][0], fila["folio"] + "-R", fila["_orden"][2])
        copia["folio"] = fila["folio"] + "-R"
        copia["lote_carga"] = f"L-{anio}-{mes:02d}-B"
        filas.append(copia)

    # defecto 2 · facturas reexportadas: mismas líneas, el mismo folio, otra carga
    documentos = sorted({(f["_orden"][0], f["folio"]) for f in filas
                         if not f["folio"].endswith("-R")})           # un doc por folio
    reexportados = set(rng.sample(documentos, 30))                    # 30 comprobantes
    for fila in list(filas):
        clave = (fila["_orden"][0], fila["folio"])
        if clave not in reexportados or fila["folio"].endswith("-R"):
            continue
        copia = dict(fila)
        copia["lote_carga"] = "L-2026-08-RC"                             # reexportación
        filas.append(copia)

    filas.sort(key=lambda f: f["_orden"])                                # como sale del sistema
    return filas


COLUMNAS_VENTAS = ["fecha", "folio", "lote_carga", "cliente_codigo", "cliente_nombre",
                   "producto_codigo", "producto_nombre", "cantidad", "unidad",
                   "precio_unitario", "importe", "vendedor"]


def escribir_csv(ruta: Path, columnas: list[str], filas: list[dict]) -> None:
    """Escribe un CSV con acentos legibles en Excel y fin de línea fijo."""
    with ruta.open("w", newline="", encoding="utf-8-sig") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=columnas, lineterminator="\n")
        escritor.writeheader()
        for fila in filas:
            escritor.writerow({c: fila[c] for c in columnas})


# ---------------------------------------------------------------------------
# 7 · Los archivos que «mandó» el cliente
# ---------------------------------------------------------------------------

def escribir_productos(ruta: Path, productos: list[dict]) -> None:
    """Catálogo de productos: un solo costo actual, sin fecha de costo."""
    filas = [{"codigo": p["codigo"], "nombre": p["nombre"], "categoria": p["categoria"],
              "unidad": p["unidad"], "costo_actual": p["costo"],
              "precio_lista_sin_iva": p["precio_lista"]} for p in productos]
    escribir_csv(ruta, ["codigo", "nombre", "categoria", "unidad", "costo_actual",
                        "precio_lista_sin_iva"], filas)


def escribir_clientes(ruta: Path, clientes: list[dict]) -> None:
    """Catálogo de clientes, con el par repetido y su RFC idéntico."""
    filas = [{"codigo": c["codigo"], "nombre": c["nombre"], "rfc": c["rfc"],
              "tipo": c["tipo"], "ciudad": c["ciudad"],
              "fecha_alta": c["fecha_alta"].isoformat(),
              "credito_dias": c["credito_dias"], "vendedor": c["vendedor"]}
             for c in clientes]
    escribir_csv(ruta, ["codigo", "nombre", "rfc", "tipo", "ciudad", "fecha_alta",
                        "credito_dias", "vendedor"], filas)


def escribir_notas(ruta: Path, notas: list[dict]) -> None:
    """Notas de crédito: el archivo está limpio; el defecto es no restarlas."""
    filas = [{"folio_nota": n["folio_nota"], "fecha_nota": n["fecha_nota"].isoformat(),
              "cliente_codigo": n["cliente"]["codigo"], "folio_factura": n["folio_factura"],
              "producto_codigo": n["producto"]["codigo"], "cantidad": n["cantidad"],
              "importe_sin_iva": importe_sin_iva_desde_con_iva(n["importe_con_iva"]),
              "importe_con_iva": n["importe_con_iva"], "motivo": n["motivo"]}
             for n in notas]
    escribir_csv(ruta, ["folio_nota", "fecha_nota", "cliente_codigo", "folio_factura",
                        "producto_codigo", "cantidad", "importe_sin_iva",
                        "importe_con_iva", "motivo"], filas)


def escribir_cartera(ruta_facturas: Path, ruta_pagos: Path,
                     facturas: list[dict], pagos: list[dict]) -> None:
    """Facturas y pagos de los últimos seis meses."""
    filas_f = [{"folio": f["folio"], "cliente_codigo": f["cliente"]["codigo"],
                "fecha_emision": f["fecha_emision"].isoformat(),
                "fecha_vencimiento": f["fecha_vencimiento"].isoformat(),
                "importe_total": f["importe"]}
               for f in sorted(facturas, key=lambda x: x["fecha_emision"])]
    escribir_csv(ruta_facturas, ["folio", "cliente_codigo", "fecha_emision",
                                 "fecha_vencimiento", "importe_total"], filas_f)

    filas_p = [{"folio_pago": f"PG-{i + 1:05d}", "fecha_pago": p["fecha_pago"].isoformat(),
                "cliente_codigo": p["cliente"]["codigo"], "factura_aplicada": p["factura"],
                "importe": p["importe"]}
               for i, p in enumerate(sorted(pagos, key=lambda x: x["fecha_pago"]))]
    escribir_csv(ruta_pagos, ["folio_pago", "fecha_pago", "cliente_codigo",
                              "factura_aplicada", "importe"], filas_p)


def escribir_compras(ruta: Path, rng: random.Random, lineas: list[dict]) -> None:
    """Egresos mensuales por proveedor: dos principales y tres menores."""
    costo_mes = {}
    for linea in lineas:                                             # costo de lo vendido
        costo_mes[etiqueta_mes(linea["fecha"].year, linea["fecha"].month)] = \
            redondear(costo_mes.get(etiqueta_mes(linea["fecha"].year,
                                                 linea["fecha"].month), 0.0)
                      + linea["costo_total"])
    filas = []
    for (anio, mes) in MESES:
        etiqueta = etiqueta_mes(anio, mes)
        base = costo_mes.get(etiqueta, 0.0) * rng.uniform(0.92, 1.08)
        fecha = date(anio, mes, 15).isoformat()
        filas.append({"fecha": fecha, "proveedor": "Distribuidora Central del Bajío",
                      "categoria": "Abarrotes",
                      "importe": redondear(base * 0.62 * (1 + IVA))})
        filas.append({"fecha": fecha, "proveedor": "Grupo Limpio de Occidente",
                      "categoria": "Limpieza",
                      "importe": redondear(base * 0.30 * (1 + IVA))})
        for proveedor, categoria, parte in [
                ("Empaques y Plásticos Tlaquepaque", "Empaque", 0.04),
                ("Transportes Ruta Sur", "Flete", 0.03),
                ("Papelería y Servicios del Sur", "Administración", 0.01)]:
            filas.append({"fecha": fecha, "proveedor": proveedor, "categoria": categoria,
                          "importe": redondear(base * parte * (1 + IVA)
                                               * rng.uniform(0.8, 1.2))})
    escribir_csv(ruta, ["fecha", "proveedor", "categoria", "importe"], filas)


def escribir_inventario(ruta: Path, rng: random.Random, lineas: list[dict],
                        productos: list[dict]) -> None:
    """Inventario por producto, con un corte de tres meses atrás."""
    venta_diaria = {}
    for linea in lineas:
        codigo = linea["producto"]["codigo"]
        if linea["fecha"] <= FECHA_CORTE_INVENTARIO:                  # hasta el corte
            venta_diaria[codigo] = venta_diaria.get(codigo, 0.0) + linea["cantidad"]
    filas = []
    for p in productos:
        if p["codigo"] not in venta_diaria:
            continue
        dias = (FECHA_CORTE_INVENTARIO - date(2025, 10, 1)).days + 1
        cobertura = rng.uniform(18, 52)                              # días de existencia
        existencia = max(0, round(venta_diaria[p["codigo"]] / dias * cobertura))
        filas.append({"producto_codigo": p["codigo"], "producto_nombre": p["nombre"],
                      "existencia": existencia,
                      "fecha_corte": FECHA_CORTE_INVENTARIO.isoformat(),
                      "costo_unitario": p["costo"]})
    escribir_csv(ruta, ["producto_codigo", "producto_nombre", "existencia",
                        "fecha_corte", "costo_unitario"], filas)


def escribir_control(ruta: Path, lineas: list[dict], notas: list[dict]) -> list[dict]:
    """Reporte mensual del dueño: es el total de control del cuadre."""
    resumen = {}
    for (anio, mes) in MESES:
        resumen[etiqueta_mes(anio, mes)] = {"bruto": 0.0, "notas": 0.0}
    for linea in lineas:
        resumen[etiqueta_mes(linea["fecha"].year, linea["fecha"].month)]["bruto"] = \
            redondear(resumen[etiqueta_mes(linea["fecha"].year,
                                           linea["fecha"].month)]["bruto"]
                      + linea["importe_con_iva"])
    for nota in notas:                                               # se cargan al mes
        etiqueta = etiqueta_mes(nota["fecha_nota"].year, nota["fecha_nota"].month)
        resumen[etiqueta]["notas"] = redondear(resumen[etiqueta]["notas"]
                                               + nota["importe_con_iva"])
    filas = []
    for (anio, mes) in MESES:
        etiqueta = etiqueta_mes(anio, mes)
        neto = redondear(resumen[etiqueta]["bruto"] - resumen[etiqueta]["notas"])
        filas.append({"mes": etiqueta,
                      "ventas_netas_con_iva": neto,
                      "ventas_netas_sin_iva": importe_sin_iva_desde_con_iva(neto)})
    escribir_csv(ruta, ["mes", "ventas_netas_con_iva", "ventas_netas_sin_iva"], filas)
    return filas


NOTA_CLIENTE = """\
Asunto: lo que alcancé a mandarle

Buen día. Le mando lo que pude sacar del sistema. Le explico lo que sí y lo
que no, para que no se confíe.

VENTAS. Le mandé el reporte de ventas de los doce meses, de octubre del año
pasado a septiembre de este. Ojo: el reporte lo saca mi contador y luego yo lo
vuelvo a bajar para mandárselo, así que puede venir algo desacomodado.

FACTURAS Y PAGOS. De aquí solo le puedo dar los últimos seis meses, de abril a
septiembre. El sistema viejo se reinstaló en marzo y para atrás ya no me da el
reporte de facturas. El de ventas sí me lo da porque lo tengo en Excel.

NOTAS DE CRÉDITO. Van aparte, en su archivo. Son las devoluciones que nos
regresan las tiendas. Yo esas las cargo al mes en que me las regresan, no al
mes en que se facturaron, porque así me lo pide el contador.

INVENTARIO. Le mando el corte del 30 de junio. No tengo uno más nuevo; el
almacenista lo levanta cada trimestre y el siguiente me toca hasta octubre.

PRODUCTOS. El costo que le mando es el que tengo hoy en el catálogo, nada más.
Costo por fecha o por lote no llevo, nunca lo he llevado.

LO QUE NO LE PUDE SACAR. El reporte de ventas no trae el almacén, así que no
le puedo decir qué se vendió de cada bodega, aunque tengo las dos. Y de los
clientes le mando el catálogo como está en el sistema, con el nombre como cada
quien lo dio de alta cuando se le abrió la cuenta.

TAMBIÉN. Somos 38 personas, dos bodegas y tres vendedores. Los dos proveedores
que nos surten casi todo son Distribuidora Central del Bajío y Grupo Limpio de
Occidente; lo demás es empaque y flete.

No le mando estados de cuenta del banco porque no los tengo a la mano y no sé
si eso se ocupe. Si lo necesita me dice.

Cualquier cosa me marca.

Distribuidora Camaleón Blanco, S.A. de C.V.
Zapopán, Jalisco
"""


# ---------------------------------------------------------------------------
# 8 · Reporte de siembra (para el operador, no para el lector del demo)
# ---------------------------------------------------------------------------

def reporte_de_siembra(lineas: list[dict], filas: list[dict], notas: list[dict],
                       facturas: list[dict], pagos: list[dict], control: list[dict],
                       marcas: dict, equivocado: dict) -> None:
    """Imprime el resumen de lo sembrado, para verificar que todo cuadra."""
    total_neto = redondear(sum(f["ventas_netas_con_iva"] for f in control))
    total_bruto = redondear(total_neto + sum(n["importe_con_iva"] for n in notas))
    saldo = redondear(sum(f["saldo"] for f in facturas))
    vencido = redondear(sum(f["saldo"] for f in facturas
                            if (CORTE - f["fecha_vencimiento"]).days > 0))
    mas_90 = redondear(sum(f["saldo"] for f in facturas
                           if (CORTE - f["fecha_vencimiento"]).days > 90))
    print("=" * 74)
    print("REPORTE DE SIEMBRA — datos sintéticos, semilla", SEMILLA)
    print("=" * 74)
    print(f"líneas de venta verdaderas ...... {len(lineas):>8,}")
    print(f"filas escritas en el archivo ..... {len(filas):>8,}")
    print(f"documentos ....................... {len({l['folio'] for l in lineas}):>8,}")
    print(f"notas de crédito ................. {len(notas):>8,}  "
          f"({redondear(sum(n['importe_con_iva'] for n in notas)):>14,.2f} con IVA)")
    print(f"facturas (6 meses) ............... {len(facturas):>8,}")
    print(f"pagos ............................ {len(pagos):>8,}")
    print(f"líneas promedio por documento .... "
          f"{len(lineas) / len({l['folio'] for l in lineas}):>8.2f}")
    print("-" * 74)
    print(f"ventas brutas con IVA ............ {total_bruto:>16,.2f}")
    print(f"ventas netas con IVA ............. {total_neto:>16,.2f}")
    print(f"ticket promedio por línea ........ {total_bruto / len(lineas):>16,.2f}")
    print(f"cartera abierta al corte ......... {saldo:>16,.2f}")
    print(f"  de eso, vencido ................. {vencido:>16,.2f}")
    print(f"  de eso, a más de 90 días ........ {mas_90:>16,.2f}")
    abiertas = sorted(f["saldo"] for f in facturas if f["saldo"] > 0)   # saldos vivos
    mediana = abiertas[len(abiertas) // 2] if abiertas else 0.0
    print(f"facturas abiertas al corte ....... {len(abiertas):>8,}")
    print(f"saldo mediano por factura abierta  {mediana:>15,.2f}")
    print("-" * 74)
    print(f"productos con margen negativo .... {', '.join(marcas['negativos'])}")
    print(f"producto renombrado a mitad ...... {marcas['renombrado']}")
    print(f"producto que más se devuelve ..... {marcas['devolvedor']}")
    if equivocado:
        print(f"pago mal aplicado ................ {equivocado['importe']:,.2f} · "
              f"{equivocado['victima']} → {equivocado['destino']}")
    print("=" * 74)


# ---------------------------------------------------------------------------
# 9 · Programa principal
# ---------------------------------------------------------------------------

def main() -> None:
    """Genera todo el corpus, en orden, con una sola semilla."""
    rng = random.Random(SEMILLA)
    RUTA_RECIBIDO.mkdir(parents=True, exist_ok=True)

    productos = construir_productos(rng)
    marcas = sembrar_defectos_de_catalogo(rng, productos)
    clientes = construir_clientes(rng)
    lineas = generar_ventas(rng, clientes, productos)
    notas = generar_notas(rng, lineas)
    facturas, pagos = generar_cartera(rng, lineas)
    equivocado = aplicar_pago_equivocado(rng, {f["folio"]: f for f in facturas}, pagos)
    filas = ensuciar_ventas(rng, lineas)

    escribir_csv(RUTA_RECIBIDO / "ventas_12_meses.csv", COLUMNAS_VENTAS, filas)
    escribir_productos(RUTA_RECIBIDO / "productos.csv", productos)
    escribir_clientes(RUTA_RECIBIDO / "clientes.csv", clientes)
    escribir_notas(RUTA_RECIBIDO / "notas_credito.csv", notas)
    escribir_cartera(RUTA_RECIBIDO / "facturas.csv", RUTA_RECIBIDO / "pagos.csv",
                     facturas, pagos)
    escribir_compras(RUTA_RECIBIDO / "compras_egresos.csv", rng, lineas)
    escribir_inventario(RUTA_RECIBIDO / "inventario.csv", rng, lineas, productos)
    control = escribir_control(RUTA_RECIBIDO / "reporte_mensual_ventas.csv",
                               lineas, notas)
    (RUTA_RECIBIDO / "nota_del_cliente.txt").write_text(NOTA_CLIENTE, encoding="utf-8")

    reporte_de_siembra(lineas, filas, notas, facturas, pagos, control, marcas,
                       equivocado)


if __name__ == "__main__":
    main()

**Los datos de este repositorio son inventados.** La empresa, sus clientes, sus productos y todas las cifras son sintéticos: prueban el método, no son trabajo hecho para un cliente.

# Cómo trabajo, paso a paso

Un cuaderno de Python que muestra el trabajo completo con los datos de una empresa, en el orden en que lo hago: lo que pedí, lo que llegó, lo que estaba mal en los datos y cuánto dinero hay en juego en cada hallazgo.

Se lee aquí en GitHub, también en el teléfono, sin instalar nada: el cuaderno está ejecutado y trae sus salidas y sus tablas.

## El caso

Una distribuidora de abarrotes y artículos de limpieza en Zapopan, Jalisco: 38 empleados, dos bodegas, tres vendedores y doce meses de operación, de octubre de 2025 a septiembre de 2026.

Los datos son inventados y traen a propósito los defectos que traen los datos de verdad: fechas escritas como texto y en dos formatos, facturas repetidas, un mes cargado dos veces, precios con y sin IVA, devoluciones que nunca se restaron, un cliente dado de alta con dos cuentas, un producto que cambió de nombre a mitad del año y un pago aplicado a la factura equivocada.

## Estado

El cuaderno va por los **pasos 1, 2, 3 y 4 de 7**:

1. ✅ Lo que pedí y lo que llegó
2. ✅ Perfilado y validación contra los totales
3. ✅ Registro de defectos
4. ✅ Supuestos declarados
5. ⬜ Hallazgos por dinero en juego
6. ⬜ Lo que estos datos no alcanzan a responder
7. ⬜ Cómo sabremos si funcionó

Mientras no estén los siete, este repositorio se queda **privado**.

## Cómo se corre

```bash
make            # reconstruye los datos sintéticos y vuelve a ejecutar el cuaderno
make datos      # solo los datos, y verifica que el cuadre cierre al centavo
make cuaderno   # solo vuelve a ejecutar el cuaderno
```

Todo está generado con una semilla fija, así que dos corridas dan exactamente los mismos números. No hace falta nada más que Python y las versiones de `requirements.txt`.

## Qué hay adentro

```
demo_efectivo.ipynb      el cuaderno, ejecutado
cuaderno/fuente.py       su fuente en texto plano, revisable en un diff
cuaderno/construir.py    convierte la fuente en el cuaderno y lo ejecuta
generar_datos.py         genera el corpus sintético con sus defectos
verificar_corpus.py      comprueba los defectos y el cuadre
datos/recibido/          los archivos que «mandó» la empresa ficticia
```

## Lo que este repositorio no tiene

- Datos de ninguna persona ni de ninguna empresa real.
- Promesas de resultado: las cifras describen una operación inventada.

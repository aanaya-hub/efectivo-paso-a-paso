**Los datos de este repositorio son inventados.** La empresa, sus clientes, sus productos y todas las cifras son sintéticos: prueban el método, no son trabajo hecho para un cliente.

# Cómo trabajo, paso a paso

Un cuaderno de Python que muestra el trabajo completo con los datos de una empresa, en el orden en que lo hago: lo que pedí, lo que llegó, lo que estaba mal en los datos y cuánto dinero hay en juego en cada hallazgo.

Se lee aquí mismo, en GitHub, también en el teléfono y sin instalar nada: el cuaderno está ejecutado y trae sus salidas, sus tablas y sus gráficas. Para leerlo no hace falta correr nada.

## El caso

Una distribuidora de abarrotes y artículos de limpieza en Zapopan, Jalisco: 38 empleados, dos bodegas, tres vendedores y doce meses de operación, de octubre de 2025 a septiembre de 2026.

Los datos son inventados y traen a propósito los defectos que traen los datos de verdad: fechas escritas como texto y en dos formatos, facturas repetidas, un mes cargado dos veces, precios con y sin IVA, devoluciones que nunca se restaron, un cliente dado de alta con dos cuentas, un producto que cambió de nombre a mitad del año y un pago aplicado a la factura equivocada.

## Los siete pasos

Cada paso abre con la explicación y sigue con el código, comentado línea por línea para quien lee Python a nivel básico.

| # | Paso | La pregunta del dueño que contesta |
| --- | --- | --- |
| 1 | Lo que pedí y lo que llegó | ¿qué me va a pedir y voy a poder dárselo? |
| 2 | Perfilado y validación contra los totales | ¿mis números cuadran? |
| 3 | Registro de defectos | ¿qué tan sucios están mis datos? |
| 4 | Supuestos declarados | ¿me está inventando algo? |
| 5 | Hallazgos por dinero en juego | ¿cuánto dinero es y qué atiendo primero? |
| 6 | Lo que estos datos NO alcanzan a responder | ¿me va a decir la verdad de lo que no sabe? |
| 7 | Cómo sabremos si funcionó | ¿esto se puede comprobar? |

## Qué va a encontrar quien lo lea

- El cuadre de la venta contra el total que reconoce el dueño, **mes por mes y al centavo**, con cada peso de la diferencia explicado.
- Ocho defectos documentados, cada uno con su evidencia y su efecto medido en pesos.
- Siete supuestos declarados, cinco de ellos con su sensibilidad calculada.
- Cinco hallazgos ordenados por monto, con cuatro gráficas, y la advertencia de que los montos no se suman entre sí porque miran la misma cartera.
- Ocho límites escritos y una negativa explícita a afirmar causalidad sin diseño.

## Cómo se corre

```bash
make            # reconstruye los datos sintéticos y vuelve a ejecutar el cuaderno
make datos      # solo los datos, y verifica que el cuadre cierre al centavo
make cuaderno   # solo vuelve a ejecutar el cuaderno
make verificar  # solo la verificación, sin regenerar nada
```

Todo está generado con una semilla fija, así que dos corridas dan exactamente los mismos números. Hace falta Python y las versiones de `requirements.txt`.

## Qué hay adentro

```
demo_efectivo.ipynb      el cuaderno, ejecutado
cuaderno/fuente.py       su fuente en texto plano, revisable en un diff
cuaderno/construir.py    convierte la fuente en el cuaderno y lo ejecuta
generar_datos.py         genera el corpus sintético con sus ocho defectos
verificar_corpus.py      comprueba los defectos y que el cuadre cierre
datos/recibido/          los archivos que «mandó» la empresa ficticia
```

## Lo que este repositorio no tiene

- Datos de ninguna persona ni de ninguna empresa real.
- Promesas de resultado: las cifras describen una operación inventada.
- Contabilidad, impuestos, asesoría legal ni de inversión. No es el alcance de este trabajo.

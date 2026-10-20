.PHONY: todo datos verificar cuaderno informe limpiar

# Reconstruye todo de cero, en orden.
todo: datos cuaderno informe

# Genera el corpus sintético y comprueba los ocho defectos y el cuadre.
datos:
	python3 generar_datos.py
	python3 verificar_corpus.py

# Vuelve a ejecutar el cuaderno desde su fuente.
cuaderno:
	python3 cuaderno/construir.py

# Arma el informe ejecutivo en PDF a partir de informe/informe.md.
informe:
	python3 informe/construir.py

# Solo la verificación (no regenera nada).
verificar:
	python3 verificar_corpus.py

# Borra lo generado. El generador lo vuelve a crear igual: semilla fija.
limpiar:
	rm -f datos/recibido/*.csv datos/recibido/nota_del_cliente.txt demo_efectivo.ipynb

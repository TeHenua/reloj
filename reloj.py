#!/usr/bin/env python3
"""Reloj grande para la consola de Linux (TTY).
Uso:  python3 reloj.py        -> HH:MM:SS
      python3 reloj.py --hm   -> HH:MM (números más grandes)
Salir: Ctrl+C
"""
import shutil
import sys
import time
from datetime import datetime

# Fuente de 5x7 "píxeles". 1 = encendido, 0 = apagado
FUENTE = {
    "0": ["11111", "10001", "10001", "10001", "10001", "10001", "11111"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["11111", "00001", "00001", "11111", "10000", "10000", "11111"],
    "3": ["11111", "00001", "00001", "01111", "00001", "00001", "11111"],
    "4": ["10001", "10001", "10001", "11111", "00001", "00001", "00001"],
    "5": ["11111", "10000", "10000", "11111", "00001", "00001", "11111"],
    "6": ["11111", "10000", "10000", "11111", "10001", "10001", "11111"],
    "7": ["11111", "00001", "00001", "00010", "00100", "00100", "00100"],
    "8": ["11111", "10001", "10001", "11111", "10001", "10001", "11111"],
    "9": ["11111", "10001", "10001", "11111", "00001", "00001", "11111"],
    ":": ["0", "0", "1", "0", "1", "0", "0"],
}
ALTO = 7
FILAS_FECHA = 2  # una línea en blanco + la línea de la fecha

# Colores de fondo ANSI: cian, verde, rojo, azul
COLORES_DIGITOS = [46, 42, 41, 44, 43, 45]
COLOR_PUNTOS = 47   # blanco
COLOR_APAGADO = 40  # negro

DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def texto_fecha(ahora, cols):
    larga = f"{DIAS[ahora.weekday()]}, {ahora.day} de {MESES[ahora.month - 1]} de {ahora.year}"
    if len(larga) <= cols:
        return larga
    return ahora.strftime("%d/%m/%Y")


def construir_frame(ahora, formato, cols, filas):
    texto = ahora.strftime(formato)

    # Cada dígito un color; la asignación rota cada minuto
    desplazamiento = ahora.minute
    colores = []
    n = 0
    for ch in texto:
        if ch == ":":
            colores.append(COLOR_PUNTOS)
        else:
            colores.append(COLORES_DIGITOS[(n + desplazamiento) % len(COLORES_DIGITOS)])
            n += 1

    # Cuadrícula de "píxeles": un código de color por píxel, fila a fila
    pix = []
    for fila in range(ALTO):
        codigos = []
        for i, ch in enumerate(texto):
            for bit in FUENTE[ch][fila]:
                codigos.append(colores[i] if bit == "1" else COLOR_APAGADO)
            if i < len(texto) - 1:  # separación entre caracteres
                codigos.append(COLOR_APAGADO)
        pix.append(codigos)
    ancho = len(pix[0])

    # Escala fraccionaria: un píxel mide 2s columnas x s filas
    s = min(cols / (ancho * 2), (filas - FILAS_FECHA) / ALTO)
    total_w = min(cols, max(ancho, round(2 * s * ancho)))
    total_h = max(ALTO, round(s * ALTO))

    # Límites de cada píxel repartiendo el espacio sobrante
    xb = [round(i * total_w / ancho) for i in range(ancho + 1)]
    yb = [round(j * total_h / ALTO) for j in range(ALTO + 1)]

    alto_total = total_h + FILAS_FECHA
    margen_sup = max(0, (filas - alto_total) // 2)
    margen_izq = max(0, (cols - total_w) // 2)

    lineas = [""] * margen_sup

    for fila in range(ALTO):
        partes = [" " * margen_izq]
        for x in range(ancho):
            w = xb[x + 1] - xb[x]
            partes.append(f"\033[{pix[fila][x]}m" + " " * w)
        lineas += ["".join(partes)] * (yb[fila + 1] - yb[fila])

    # Fecha centrada, con el color del primer dígito
    lineas.append("")
    fecha = texto_fecha(ahora, cols)
    color_fg = colores[0] - 10  # fondo 4x -> texto 3x
    lineas.append(" " * max(0, (cols - len(fecha)) // 2) + f"\033[1;{color_fg}m{fecha}")

    # Sin salto de línea tras la última fila, para que no se desplace la pantalla
    return "\033[H" + "\n".join(l + "\033[0m\033[K" for l in lineas) + "\033[J"


def main():
    formato = "%H:%M" if "--hm" in sys.argv else "%H:%M:%S"

    sys.stdout.write("\033[2J\033[?25l")  # limpiar pantalla y ocultar cursor
    try:
        while True:
            cols, filas = shutil.get_terminal_size((80, 25))
            sys.stdout.write(construir_frame(datetime.now(), formato, cols, filas))
            sys.stdout.flush()
            time.sleep(1 - (time.time() % 1))  # esperar al siguiente segundo
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\033[0m\033[?25h\033[2J\033[H")  # restaurar consola
        sys.stdout.flush()


if __name__ == "__main__":
    main()
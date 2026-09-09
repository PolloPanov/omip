import os
import sys
import threading
import tkinter as tk
from tkinter import messagebox, simpledialog

import historico_omip


def obtener_carpeta_base():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


BASE_DIR = obtener_carpeta_base()
os.chdir(BASE_DIR)


def ejecutar_30_dias():
    try:
        historico_omip.generar_30_dias(enviar_telegram=True)
        messagebox.showinfo(
            "OMIP",
            "La gráfica de los últimos 30 días se ha generado correctamente "
            "y se ha enviado a Telegram."
        )
    except Exception as e:
        messagebox.showerror(
            "Error",
            f"No se ha podido generar la gráfica:\n\n{e}"
        )


def ejecutar_mes(anio, mes):
    try:
        historico_omip.generar_mes(
            anio,
            mes,
            enviar_telegram=True
        )
        messagebox.showinfo(
            "OMIP",
            f"La gráfica de {mes:02d}/{anio} se ha generado correctamente "
            "y se ha enviado a Telegram."
        )
    except Exception as e:
        messagebox.showerror(
            "Error",
            f"No se ha podido generar la gráfica:\n\n{e}"
        )


def ultimos_30_dias():
    threading.Thread(
        target=ejecutar_30_dias,
        daemon=True
    ).start()


def mes_concreto():
    anio = simpledialog.askinteger(
        "Mes concreto",
        "Introduce el año:",
        minvalue=2020,
        maxvalue=2100,
        parent=ventana
    )

    if anio is None:
        return

    mes = simpledialog.askinteger(
        "Mes concreto",
        "Introduce el mes (1-12):",
        minvalue=1,
        maxvalue=12,
        parent=ventana
    )

    if mes is None:
        return

    threading.Thread(
        target=ejecutar_mes,
        args=(anio, mes),
        daemon=True
    ).start()


ventana = tk.Tk()
ventana.title("Gráficas Históricas OMIP")
ventana.geometry("560x360")
ventana.resizable(False, False)


titulo = tk.Label(
    ventana,
    text="GRÁFICAS HISTÓRICAS OMIP",
    font=("Arial", 20, "bold")
)
titulo.pack(pady=(30, 25))


boton_30 = tk.Button(
    ventana,
    text="ÚLTIMOS 30 DÍAS",
    command=ultimos_30_dias,
    font=("Arial", 16, "bold"),
    height=3,
    width=30
)
boton_30.pack(pady=10)


boton_mes = tk.Button(
    ventana,
    text="MES CONCRETO",
    command=mes_concreto,
    font=("Arial", 16, "bold"),
    height=3,
    width=30
)
boton_mes.pack(pady=10)


pie = tk.Label(
    ventana,
    text="Las gráficas se guardan en graficas_historicas",
    font=("Arial", 9)
)
pie.pack(pady=15)


ventana.mainloop()

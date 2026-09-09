import os
import sys
import threading
import tkinter as tk
from tkinter import messagebox, simpledialog

from historico_omip import (
    extraer_historico,
    generar_30_dias,
    generar_trimestre,
)


def obtener_carpeta_base():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)

    return os.path.dirname(
        os.path.abspath(__file__)
    )


BASE_DIR = obtener_carpeta_base()

os.chdir(BASE_DIR)


def ejecutar(funcion, *args):
    try:
        historico = extraer_historico()

        if historico.empty:
            messagebox.showerror(
                "OMIP",
                "No se encontraron datos históricos en los CSV diarios.",
            )
            return

        root.config(cursor="wait")
        root.update()

        creada = funcion(
            historico,
            *args,
        )

        root.config(cursor="")

        if creada:
            messagebox.showinfo(
                "OMIP",
                "Gráfica generada correctamente y enviada a Telegram.",
            )
        else:
            messagebox.showwarning(
                "OMIP",
                "No se pudo generar o enviar la gráfica.",
            )

    except Exception as exc:
        root.config(cursor="")

        messagebox.showerror(
            "OMIP",
            f"Se produjo un error:\n\n{exc}",
        )


def ejecutar_en_hilo(
    funcion,
    *args,
):
    hilo = threading.Thread(
        target=ejecutar,
        args=(funcion, *args),
        daemon=True,
    )

    hilo.start()


def ultimos_30():
    ejecutar_en_hilo(
        generar_30_dias
    )


def trimestre_concreto():
    anio = simpledialog.askinteger(
        "Trimestre concreto",
        "Introduce el año (ej. 2027):",
        minvalue=2000,
        maxvalue=2100,
        parent=root,
    )

    if anio is None:
        return

    trimestre = simpledialog.askinteger(
        "Trimestre concreto",
        "Introduce el trimestre (1, 2, 3 o 4):",
        minvalue=1,
        maxvalue=4,
        parent=root,
    )

    if trimestre is None:
        return

    ejecutar_en_hilo(
        generar_trimestre,
        anio,
        trimestre,
    )


root = tk.Tk()

root.title(
    "Gráficas Históricas OMIP"
)

root.geometry(
    "600x400"
)

root.resizable(
    False,
    False,
)

root.configure(
    padx=35,
    pady=30,
)


label = tk.Label(
    root,
    text="GRÁFICAS HISTÓRICAS OMIP",
    font=(
        "Segoe UI",
        22,
        "bold",
    ),
)

label.pack(
    pady=(0, 8)
)


subtitle = tk.Label(
    root,
    text="Selecciona la gráfica que quieres generar",
    font=(
        "Segoe UI",
        11,
    ),
)

subtitle.pack(
    pady=(0, 25)
)


btn30 = tk.Button(
    root,
    text="📈  Últimos 30 días",
    command=ultimos_30,
    font=(
        "Segoe UI",
        17,
        "bold",
    ),
    height=2,
    width=28,
)

btn30.pack(
    pady=10
)


btntrimestre = tk.Button(
    root,
    text="📊  Trimestre concreto",
    command=trimestre_concreto,
    font=(
        "Segoe UI",
        17,
        "bold",
    ),
    height=2,
    width=28,
)

btntrimestre.pack(
    pady=10
)


footer = tk.Label(
    root,
    text=(
        "La gráfica se guarda y se envía automáticamente a Telegram"
    ),
    font=(
        "Segoe UI",
        9,
    ),
)

footer.pack(
    pady=(20, 0)
)


root.mainloop()

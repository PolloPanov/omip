import os
import sys
import threading
import tkinter as tk
from tkinter import messagebox, ttk

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


def ejecutar_en_hilo(funcion, *args):
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
    ventana = tk.Toplevel(root)

    ventana.title(
        "Trimestre concreto"
    )

    ventana.geometry(
        "430x300"
    )

    ventana.resizable(
        False,
        False,
    )

    ventana.transient(root)
    ventana.grab_set()

    marco = tk.Frame(
        ventana,
        padx=30,
        pady=25,
    )

    marco.pack(
        fill="both",
        expand=True,
    )

    titulo = tk.Label(
        marco,
        text="SELECCIONA EL TRIMESTRE",
        font=(
            "Segoe UI",
            17,
            "bold",
        ),
    )

    titulo.pack(
        pady=(0, 25)
    )

    # Años disponibles.
    anios = [
        str(anio)
        for anio in range(
            2026,
            2031,
        )
    ]

    tk.Label(
        marco,
        text="Año:",
        font=(
            "Segoe UI",
            11,
        ),
    ).pack(
        anchor="w"
    )

    combo_anio = ttk.Combobox(
        marco,
        values=anios,
        state="readonly",
        font=(
            "Segoe UI",
            12,
        ),
        width=25,
    )

    combo_anio.pack(
        pady=(5, 18)
    )

    combo_anio.current(0)

    tk.Label(
        marco,
        text="Trimestre:",
        font=(
            "Segoe UI",
            11,
        ),
    ).pack(
        anchor="w"
    )

    trimestres = [
        "Q1",
        "Q2",
        "Q3",
        "Q4",
    ]

    combo_trimestre = ttk.Combobox(
        marco,
        values=trimestres,
        state="readonly",
        font=(
            "Segoe UI",
            12,
        ),
        width=25,
    )

    combo_trimestre.pack(
        pady=(5, 20)
    )

    combo_trimestre.current(0)

    def generar():
        try:
            anio = int(
                combo_anio.get()
            )

            trimestre_texto = (
                combo_trimestre.get()
            )

            trimestre = int(
                trimestre_texto[1]
            )

            ventana.destroy()

            ejecutar_en_hilo(
                generar_trimestre,
                anio,
                trimestre,
            )

        except Exception as exc:
            messagebox.showerror(
                "OMIP",
                f"No se pudo seleccionar el trimestre:\n\n{exc}",
                parent=ventana,
            )

    boton_generar = tk.Button(
        marco,
        text="GENERAR GRÁFICA",
        command=generar,
        font=(
            "Segoe UI",
            12,
            "bold",
        ),
        height=2,
        width=24,
    )

    boton_generar.pack(
        pady=(5, 0)
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

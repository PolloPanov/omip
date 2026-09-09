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


def obtener_trimestres_disponibles(historico):
    """
    Obtiene los contratos trimestrales que realmente existen
    en los CSV históricos.

    Devuelve un diccionario con esta estructura:

        {
            2026: [4],
            2027: [1, 2, 3, 4],
            2028: [1, 2]
        }
    """

    if historico.empty:
        return {}

    contratos = (
        historico["contrato"]
        .dropna()
        .astype(str)
        .str.strip()
    )

    disponibles = {}

    for contrato in contratos.unique():

        match = __import__("re").match(
            r"^Q([1-4])-(\d{2})$",
            contrato,
        )

        if not match:
            continue

        trimestre = int(
            match.group(1)
        )

        anio_corto = int(
            match.group(2)
        )

        # Los contratos OMIP utilizan los dos últimos dígitos.
        # 00-79 -> 2000-2079
        # 80-99 -> 2080-2099
        # En la práctica actual trabajamos con 2026 en adelante.
        if anio_corto < 80:
            anio = 2000 + anio_corto
        else:
            anio = 1900 + anio_corto

        if anio not in disponibles:
            disponibles[anio] = []

        if trimestre not in disponibles[anio]:
            disponibles[anio].append(
                trimestre
            )

    for anio in disponibles:
        disponibles[anio].sort()

    return dict(
        sorted(
            disponibles.items()
        )
    )


def trimestre_concreto():

    try:
        historico = extraer_historico()

        disponibles = obtener_trimestres_disponibles(
            historico
        )

    except Exception as exc:
        messagebox.showerror(
            "OMIP",
            f"No se pudieron leer los datos históricos:\n\n{exc}",
            parent=root,
        )
        return

    if not disponibles:
        messagebox.showwarning(
            "OMIP",
            "No se encontraron contratos trimestrales con datos.",
            parent=root,
        )
        return

    ventana = tk.Toplevel(root)

    ventana.title(
        "Trimestre concreto"
    )

    ventana.geometry(
        "430x330"
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

    # ---------------------------------------------------------
    # DESPLEGABLE DE AÑO
    # ---------------------------------------------------------

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

    anios = [
        str(anio)
        for anio in disponibles.keys()
    ]

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

    # ---------------------------------------------------------
    # DESPLEGABLE DE TRIMESTRE
    # ---------------------------------------------------------

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

    combo_trimestre = ttk.Combobox(
        marco,
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

    def actualizar_trimestres(event=None):

        try:
            anio = int(
                combo_anio.get()
            )

            trimestres_anio = disponibles.get(
                anio,
                [],
            )

            opciones = [
                f"Q{trimestre}"
                for trimestre in trimestres_anio
            ]

            combo_trimestre["values"] = opciones

            if opciones:
                combo_trimestre.current(0)

        except Exception:
            combo_trimestre["values"] = []

    combo_anio.bind(
        "<<ComboboxSelected>>",
        actualizar_trimestres,
    )

    combo_anio.current(0)

    actualizar_trimestres()

    # ---------------------------------------------------------
    # BOTÓN GENERAR
    # ---------------------------------------------------------

    def generar():

        try:
            if not combo_anio.get():
                messagebox.showwarning(
                    "OMIP",
                    "Selecciona un año.",
                    parent=ventana,
                )
                return

            if not combo_trimestre.get():
                messagebox.showwarning(
                    "OMIP",
                    "Selecciona un trimestre.",
                    parent=ventana,
                )
                return

            anio = int(
                combo_anio.get()
            )

            trimestre = int(
                combo_trimestre
                .get()
                .replace("Q", "")
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


# =============================================================
# VENTANA PRINCIPAL
# =============================================================

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

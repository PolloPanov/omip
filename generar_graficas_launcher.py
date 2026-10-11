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

    return os.path.dirname(os.path.abspath(__file__))


BASE_DIR = obtener_carpeta_base()
os.chdir(BASE_DIR)


def ruta_grafica(funcion, args):
    carpeta = os.path.join(BASE_DIR, "graficas_historicas")

    if funcion is generar_30_dias:
        nombre = "omip_ultimos_30_dias_trimestral.png"
    else:
        anio, trimestre = args
        codigo = f"Q{trimestre}-{str(anio)[-2:]}"
        nombre = f"omip_{codigo}.png"

    return os.path.join(carpeta, nombre)


def mostrar_resultado(creada, ruta, error=None):
    root.config(cursor="")
    btn30.config(state="normal")
    btntrimestre.config(state="normal")

    if error is not None:
        messagebox.showerror(
            "OMIP",
            f"Se produjo un error:\n\n{error}",
            parent=root,
        )
        return

    if creada and os.path.isfile(ruta):
        try:
            # En Windows abre la gráfica con la aplicación predeterminada para PNG.
            os.startfile(ruta)
        except OSError as exc:
            messagebox.showwarning(
                "OMIP",
                "La gráfica se ha guardado, pero Windows no pudo abrirla automáticamente.\n\n"
                f"Puedes encontrarla aquí:\n{ruta}\n\nDetalle: {exc}",
                parent=root,
            )
            return

        messagebox.showinfo(
            "OMIP",
            f"Gráfica generada y abierta correctamente.\n\nGuardada en:\n{ruta}\n\n"
            "No se ha enviado nada a Telegram.",
            parent=root,
        )
    else:
        messagebox.showwarning(
            "OMIP",
            "No se pudo generar la gráfica. Comprueba que los CSV históricos contienen datos.",
            parent=root,
        )


def ejecutar(funcion, *args):
    root.after(0, lambda: root.config(cursor="wait"))
    root.after(0, lambda: btn30.config(state="disabled"))
    root.after(0, lambda: btntrimestre.config(state="disabled"))

    def trabajo():
        try:
            historico = extraer_historico()

            if historico.empty:
                root.after(
                    0,
                    lambda: mostrar_resultado(
                        False,
                        "",
                        "No se encontraron datos históricos en los CSV diarios.",
                    ),
                )
                return

            # El programa de escritorio genera y guarda la gráfica localmente.
            # Telegram queda desactivado en este flujo.
            creada = funcion(
                historico,
                *args,
                enviar_telegram=False,
            )
            ruta = ruta_grafica(funcion, args)

            root.after(
                0,
                lambda: mostrar_resultado(creada, ruta),
            )

        except Exception as exc:
            error = str(exc)
            root.after(
                0,
                lambda error=error: mostrar_resultado(
                    False,
                    "",
                    error,
                ),
            )

    threading.Thread(target=trabajo, daemon=True).start()


def ultimos_30():
    ejecutar(generar_30_dias)


def obtener_trimestres_disponibles(historico):
    """Devuelve los años y trimestres disponibles en los CSV históricos."""
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
        import re

        match = re.match(r"^Q([1-4])-(\d{2})$", contrato)
        if not match:
            continue

        trimestre = int(match.group(1))
        anio_corto = int(match.group(2))
        anio = 2000 + anio_corto if anio_corto < 80 else 1900 + anio_corto

        disponibles.setdefault(anio, [])
        if trimestre not in disponibles[anio]:
            disponibles[anio].append(trimestre)

    for anio in disponibles:
        disponibles[anio].sort()

    return dict(sorted(disponibles.items()))


def trimestre_concreto():
    try:
        historico = extraer_historico()
        disponibles = obtener_trimestres_disponibles(historico)
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
    ventana.title("Trimestre concreto")
    ventana.geometry("430x330")
    ventana.resizable(False, False)
    ventana.transient(root)
    ventana.grab_set()

    marco = tk.Frame(ventana, padx=30, pady=25)
    marco.pack(fill="both", expand=True)

    tk.Label(
        marco,
        text="SELECCIONA EL TRIMESTRE",
        font=("Segoe UI", 17, "bold"),
    ).pack(pady=(0, 25))

    tk.Label(marco, text="Año:", font=("Segoe UI", 11)).pack(anchor="w")

    anios = [str(anio) for anio in disponibles]
    combo_anio = ttk.Combobox(
        marco, values=anios, state="readonly",
        font=("Segoe UI", 12), width=25,
    )
    combo_anio.pack(pady=(5, 18))

    tk.Label(marco, text="Trimestre:", font=("Segoe UI", 11)).pack(anchor="w")

    combo_trimestre = ttk.Combobox(
        marco, state="readonly", font=("Segoe UI", 12), width=25,
    )
    combo_trimestre.pack(pady=(5, 20))

    def actualizar_trimestres(event=None):
        try:
            anio = int(combo_anio.get())
            opciones = [f"Q{t}" for t in disponibles.get(anio, [])]
            combo_trimestre["values"] = opciones
            if opciones:
                combo_trimestre.current(0)
        except (ValueError, tk.TclError):
            combo_trimestre["values"] = []

    combo_anio.bind("<<ComboboxSelected>>", actualizar_trimestres)
    combo_anio.current(0)
    actualizar_trimestres()

    def generar():
        if not combo_anio.get():
            messagebox.showwarning("OMIP", "Selecciona un año.", parent=ventana)
            return
        if not combo_trimestre.get():
            messagebox.showwarning("OMIP", "Selecciona un trimestre.", parent=ventana)
            return

        anio = int(combo_anio.get())
        trimestre = int(combo_trimestre.get().replace("Q", ""))
        ventana.destroy()
        ejecutar(generar_trimestre, anio, trimestre)

    tk.Button(
        marco,
        text="GENERAR GRÁFICA",
        command=generar,
        font=("Segoe UI", 12, "bold"),
        height=2,
        width=24,
    ).pack(pady=(5, 0))


root = tk.Tk()
root.title("Gráficas Históricas OMIP")
root.geometry("600x400")
root.resizable(False, False)
root.configure(padx=35, pady=30)

tk.Label(
    root,
    text="GRÁFICAS HISTÓRICAS OMIP",
    font=("Segoe UI", 22, "bold"),
).pack(pady=(0, 8))

tk.Label(
    root,
    text="Selecciona la gráfica que quieres generar",
    font=("Segoe UI", 11),
).pack(pady=(0, 25))

btn30 = tk.Button(
    root,
    text="📈  Últimos 30 días",
    command=ultimos_30,
    font=("Segoe UI", 17, "bold"),
    height=2,
    width=28,
)
btn30.pack(pady=10)

btntrimestre = tk.Button(
    root,
    text="📊  Trimestre concreto",
    command=trimestre_concreto,
    font=("Segoe UI", 17, "bold"),
    height=2,
    width=28,
)
btntrimestre.pack(pady=10)

tk.Label(
    root,
    text="Las gráficas se guardan en el PC y se abren en Windows. No se envían a Telegram.",
    font=("Segoe UI", 9),
).pack(pady=(20, 0))

root.mainloop()

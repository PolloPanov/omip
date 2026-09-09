import os
import subprocess
import sys
import tkinter as tk
from tkinter import messagebox, simpledialog

ROOT = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(ROOT, "historico_omip.py")


def python_executable():
    venv = os.path.join(ROOT, ".venv", "Scripts", "python.exe")
    return venv if os.path.exists(venv) else sys.executable


def ejecutar(args):
    try:
        subprocess.Popen([python_executable(), SCRIPT, *args], cwd=ROOT)
        messagebox.showinfo("OMIP", "La generación de la gráfica se ha iniciado.\n\nSe guardará en graficas_historicas y se enviará a Telegram.")
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo iniciar la generación:\n\n{e}")


def ultimos_30():
    ejecutar(["--30-dias"])


def mes_concreto():
    anio = simpledialog.askinteger("Mes concreto", "Introduce el año (ej. 2026):", minvalue=2000, maxvalue=2100, parent=root)
    if anio is None:
        return
    mes = simpledialog.askinteger("Mes concreto", "Introduce el mes (1-12):", minvalue=1, maxvalue=12, parent=root)
    if mes is not None:
        ejecutar(["--mes", str(anio), str(mes)])


root = tk.Tk()
root.title("Gráficas Históricas OMIP")
root.geometry("560x360")
root.resizable(False, False)
root.configure(padx=30, pady=25)

tk.Label(root, text="GRÁFICAS HISTÓRICAS OMIP", font=("Segoe UI", 20, "bold")).pack(pady=(0, 8))
tk.Label(root, text="Elige qué gráfica quieres generar", font=("Segoe UI", 11)).pack(pady=(0, 25))

tk.Button(root, text="Últimos 30 días", command=ultimos_30, font=("Segoe UI", 16, "bold"), height=2, width=28).pack(pady=10)
tk.Button(root, text="Mes concreto", command=mes_concreto, font=("Segoe UI", 16, "bold"), height=2, width=28).pack(pady=10)

tk.Label(root, text="Las gráficas se guardan y se envían a Telegram", font=("Segoe UI", 9)).pack(pady=(18, 0))
root.mainloop()

import tkinter as tk
from tkinter import messagebox, simpledialog

from historico_omip import extraer_historico, generar_30_dias, generar_mes


def ejecutar(funcion, *args):
    try:
        historico = extraer_historico()
        if historico.empty:
            messagebox.showerror("OMIP", "No se encontraron datos históricos en los CSV diarios.")
            return
        root.config(cursor="wait")
        root.update()
        creada = funcion(historico, *args)
        root.config(cursor="")
        if creada:
            messagebox.showinfo("OMIP", "Gráfica generada correctamente y enviada a Telegram.")
        else:
            messagebox.showwarning("OMIP", "No se pudo generar la gráfica con los datos disponibles.")
    except Exception as e:
        root.config(cursor="")
        messagebox.showerror("OMIP", f"Se produjo un error:\n\n{e}")


def ultimos_30():
    ejecutar(generar_30_dias)


def mes_concreto():
    anio = simpledialog.askinteger("Mes concreto", "Introduce el año (ej. 2026):", minvalue=2000, maxvalue=2100, parent=root)
    if anio is None:
        return
    mes = simpledialog.askinteger("Mes concreto", "Introduce el mes (1-12):", minvalue=1, maxvalue=12, parent=root)
    if mes is None:
        return
    ejecutar(generar_mes, anio, mes)


root = tk.Tk()
root.title("Gráficas Históricas OMIP")
root.geometry("600x400")
root.resizable(False, False)
root.configure(padx=35, pady=30)

label = tk.Label(root, text="GRÁFICAS HISTÓRICAS OMIP", font=("Segoe UI", 22, "bold"))
label.pack(pady=(0, 8))

subtitle = tk.Label(root, text="Selecciona la gráfica que quieres generar", font=("Segoe UI", 11))
subtitle.pack(pady=(0, 25))

btn30 = tk.Button(root, text="📈  Últimos 30 días", command=ultimos_30, font=("Segoe UI", 17, "bold"), height=2, width=28)
btn30.pack(pady=10)

btnmes = tk.Button(root, text="📊  Mes concreto", command=mes_concreto, font=("Segoe UI", 17, "bold"), height=2, width=28)
btnmes.pack(pady=10)

footer = tk.Label(root, text="La gráfica se guarda y se envía automáticamente a Telegram", font=("Segoe UI", 9))
footer.pack(pady=(20, 0))

root.mainloop()

import os
import subprocess
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BAT = os.path.join(BASE_DIR, "generar_graficas.bat")

if not os.path.exists(BAT):
    print("No se encuentra generar_graficas.bat")
    input("Pulsa Enter para salir...")
    sys.exit(1)

subprocess.call(["cmd.exe", "/c", BAT], cwd=BASE_DIR)

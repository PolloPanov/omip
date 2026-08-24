import datetime
import io
import os
import re
from bs4 import BeautifulSoup
import pandas as pd
import requests

# Importar las funciones de los módulos auxiliares
from graficar_omip import generar_grafico_omip
from telegram_bot import (
    dar_formato_resumen_omip,
    enviar_imagen_telegram,
    enviar_mensaje_telegram,
)


def obtener_precios_omip():
    """Realiza el scraping de los precios futuros del mercado OMIP."""
    url = "https://www.omip.pt/es/dados-mercado"
    print(f"[{datetime.datetime.now()}] Conectando a OMIP ({url})...")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        )
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Error al conectar con OMIP: {e}")
        return None

    soup = BeautifulSoup(response.content, "html.parser")
    tablas = soup.find_all("table")

    if not tablas:
        print("❌ No se encontraron tablas en la página de OMIP.")
        return None

    # Parsear usando StringIO y forzando el motor lxml para evitar dependencias faltantes
    html_str = str(tablas[0])
    df_lista = pd.read_html(io.StringIO(html_str), flavor="lxml")
    if not df_lista:
        print("❌ No se pudieron procesar las tablas HTML.")
        return None

    df = df_lista[0]

    # Añadir columna con la fecha de extracción
    df["Fecha_Extraccion"] = datetime.date.today().strftime("%Y-%m-%d")

    return df


def guardar_resultados(df):
    """Guarda los datos extraídos en CSV y Excel."""
    if df is None or df.empty:
        return

    fecha_str = datetime.date.today().strftime("%Y%m%d")
    archivo_csv = f"omip_futuros_{fecha_str}.csv"
    archivo_excel = f"omip_futuros_{fecha_str}.xlsx"

    df.to_csv(archivo_csv, index=False, encoding="utf-8-sig")
    df.to_excel(archivo_excel, index=False)

    print("\n✅ Datos guardados con éxito:")
    print(f"   - {archivo_csv}")
    print(f"   - {archivo_excel}")


if __name__ == "__main__":
    # 1. Extraer datos del mercado OMIP
    df_omip = obtener_precios_omip()

    if df_omip is not None and not df_omip.empty:
        print("\n--- RESUMEN DE PRECIOS A FUTURO (OMIP) ---")
        print(df_omip.head(10))

        # 2. Guardar CSV y Excel
        guardar_resultados(df_omip)

        # 3. Generar el gráfico PNG de la curva de precios
        ruta_grafico = generar_grafico_omip(df_omip)

        # 4. Formatear y enviar mensaje + imagen a Telegram
        texto_resumen = dar_formato_resumen_omip(df_omip)

        # Enviar primero el texto
        enviar_mensaje_telegram(texto_resumen)

        # Enviar la imagen del gráfico tras verificar su existencia
        if ruta_grafico and os.path.exists(ruta_grafico):
            print(f"🚀 Enviando gráfico '{ruta_grafico}' a Telegram...")
            enviar_imagen_telegram(
                ruta_imagen=ruta_grafico,
                caption="📈 <i>Curva de precios a futuro OMIP</i>",
            )
        else:
            print(
                f"⚠️ No se pudo enviar el gráfico. Archivo no encontrado:"
                f" {ruta_grafico}"
            )
    else:
        print("❌ No se pudieron obtener o procesar datos de OMIP.")
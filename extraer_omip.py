import datetime
import io
import os
import re
from bs4 import BeautifulSoup
import pandas as pd
import requests

from graficar_omip import generar_grafico_omip
from telegram_bot import (
    dar_formato_resumen_omip,
    enviar_imagen_telegram,
    enviar_mensaje_telegram,
)


def obtener_precios_omip():
    """Scrapea la vista unificada y los distintos vencimientos para obtener 365 días de futuros."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        )
    }

    # URLs a consultar: vista general y vencimientos específicos (Días, Meses, Trimestres, Años)
    urls = [
        "https://www.omip.pt/es/plazo-hoy",
        "https://www.omip.pt/es/dados-mercado?product=EL&zone=ES&instrument=FTB&maturity=D",
        "https://www.omip.pt/es/dados-mercado?product=EL&zone=ES&instrument=FTB&maturity=M",
        "https://www.omip.pt/es/dados-mercado?product=EL&zone=ES&instrument=FTB&maturity=Q",
        "https://www.omip.pt/es/dados-mercado?product=EL&zone=ES&instrument=FTB&maturity=YR",
    ]

    dfs = []
    print(f"[{datetime.datetime.now()}] Extrayendo datos a 365 días de OMIP...")

    for url in urls:
        try:
            res = requests.get(url, headers=headers, timeout=12)
            if res.status_code != 200:
                continue

            soup = BeautifulSoup(res.content, "html.parser")
            tablas = soup.find_all("table")

            for tabla in tablas:
                html_str = str(tabla)
                df_temp_list = pd.read_html(io.StringIO(html_str), flavor="lxml")
                if df_temp_list:
                    df_t = df_temp_list[0]
                    if not df_t.empty and len(df_t.columns) > 1:
                        dfs.append(df_t)
        except Exception:
            continue

    if not dfs:
        print("❌ No se pudieron procesar las tablas de OMIP.")
        return None

    # Concatenar todos los vencimientos y eliminar filas duplicadas
    df_completo = pd.concat(dfs, ignore_index=True)
    df_completo.drop_duplicates(inplace=True)
    df_completo["Fecha_Extraccion"] = datetime.date.today().strftime("%Y-%m-%d")

    return df_completo


def guardar_resultados(df):
    """Guarda los datos extraídos en CSV y Excel."""
    if df is None or df.empty:
        return

    fecha_str = datetime.date.today().strftime("%Y%m%d")
    archivo_csv = f"omip_futuros_365d_{fecha_str}.csv"
    archivo_excel = f"omip_futuros_365d_{fecha_str}.xlsx"

    df.to_csv(archivo_csv, index=False, encoding="utf-8-sig")
    df.to_excel(archivo_excel, index=False)

    print(f"\n✅ Archivos de 365 días guardados:")
    print(f"   - {archivo_csv}")
    print(f"   - {archivo_excel}")


if __name__ == "__main__":
    df_omip = obtener_precios_omip()

    if df_omip is not None and not df_omip.empty:
        print(f"\n--- DATOS DE CONTRATOS OMIP EXTRAÍDOS ({len(df_omip)} filas) ---")
        print(df_omip.head(15))

        # 1. Guardar archivos de datos
        guardar_resultados(df_omip)

        # 2. Generar gráfico completo
        ruta_grafico = generar_grafico_omip(df_omip)

        # 3. Formatear y enviar mensaje a Telegram
        texto_resumen = dar_formato_resumen_omip(df_omip)
        enviar_mensaje_telegram(texto_resumen)

        if ruta_grafico and os.path.exists(ruta_grafico):
            print("🚀 Enviando gráfico completo a Telegram...")
            enviar_imagen_telegram(
                ruta_imagen=ruta_grafico,
                caption="📈 <i>Curva completa de precios a futuro OMIP (365 Días)</i>",
            )
        else:
            print(f"⚠️ No se encontró la imagen del gráfico: {ruta_grafico}")
    else:
        print("❌ No se pudieron obtener datos de OMIP.")
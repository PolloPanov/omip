import sys
import datetime
import pandas as pd
import requests
from bs4 import BeautifulSoup


def obtener_precios_omip():
    """Extrae la tabla de cierres y liquidación de futuros de OMIP."""
    url = "https://www.omip.pt/es/dados-mercado"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/115.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    }

    print(f"[{datetime.datetime.now()}] Conectando a OMIP ({url})...")

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error al conectar con la web de OMIP: {e}")
        sys.exit(1)

    soup = BeautifulSoup(response.text, "html.parser")

    # Localizar las tablas de datos de mercado
    tablas = soup.find_all("table")

    if not tablas:
        print(
            "No se encontraron tablas de datos. Es posible que el diseño HTML haya cambiado."
        )
        sys.exit(1)

    registros = []

    # Iterar sobre la primera tabla de mercado de futuros
    tabla_futuros = tablas[0]
    filas = tabla_futuros.find_all("tr")

    for fila in filas:
        celdas = fila.find_all(["td", "th"])
        datos_fila = [celda.text.strip() for celda in celdas]

        # Validar que la fila contenga datos útiles (evitar cabeceras vacías)
        if len(datos_fila) >= 4 and datos_fila[0] != "":
            registros.append(datos_fila)

    if not registros:
        print("No se pudieron extraer filas válidas de la tabla.")
        sys.exit(1)

    # Convertir a DataFrame de Pandas
    cabecera = registros[0]
    datos = registros[1:]

    df = pd.DataFrame(datos, columns=cabecera)

    # Limpieza de datos
    # 1. Renombrar columnas clave si es necesario
    df.columns = [c.strip() for c in df.columns]

    # 2. Convertir precios a tipo float (reemplazando coma decimal por punto)
    for col in df.columns:
        if "precio" in col.lower() or "cierre" in col.lower() or "settlement" in col.lower() or "último" in col.lower():
            df[col] = (
                df[col]
                .str.replace(".", "", regex=False)
                .str.replace(",", ".", regex=False)
            )
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Añadir columna con la fecha de extracción
    df["Fecha_Extraccion"] = datetime.date.today().strftime("%Y-%m-%d")

    return df


def guardar_resultados(df):
    """Guarda los datos extraídos en CSV y Excel."""
    fecha_str = datetime.date.today().strftime("%Y%m%d")
    archivo_csv = f"omip_futuros_{fecha_str}.csv"
    archivo_excel = f"omip_futuros_{fecha_str}.xlsx"

    df.to_csv(archivo_csv, index=False, encoding="utf-8-sig")
    df.to_excel(archivo_excel, index=False)

    print(f"\n✅ Datos guardados con éxito:")
    print(f"   - {archivo_csv}")
    print(f"   - {archivo_excel}")


# Importar las funciones de los otros archivos que creaste
from graficar_omip import generar_grafico_omip
from telegram_bot import dar_formato_resumen_omip, enviar_mensaje_telegram, enviar_imagen_telegram

if __name__ == "__main__":
    # 1. Extraer datos del mercado OMIP
    df_omip = obtener_precios_omip()
    
    print("\n--- RESUMEN DE PRECIOS A FUTURO (OMIP) ---")
    print(df_omip.head(10))
    
    # 2. Guardar CSV y Excel
    guardar_resultados(df_omip)
    
    # 3. Generar el gráfico PNG de la curva de precios
    ruta_grafico = generar_grafico_omip(df_omip)
    
    # 4. Formatear y enviar mensaje + imagen a Telegram
    texto_resumen = dar_formato_resumen_omip(df_omip)
    enviar_mensaje_telegram(texto_resumen)
    
    if ruta_grafico:
        enviar_imagen_telegram(ruta_grafico, caption="📈 Curva de precios a futuro OMIP")
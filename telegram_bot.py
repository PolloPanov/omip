import os
import re
import pandas as pd
import requests


def enviar_mensaje_telegram(mensaje, bot_token=None, chat_id=None):
    """Envía un mensaje de texto formateado en HTML a Telegram."""
    token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
    cid = chat_id or os.getenv("TELEGRAM_CHAT_ID")

    if not token or not cid:
        print("⚠️ Credenciales de Telegram no configuradas. Saltando envío.")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": cid,
        "text": mensaje,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    response = requests.post(url, data=payload, timeout=10)
    if response.status_code == 200:
        print("💬 Mensaje enviado correctamente a Telegram.")
    else:
        print(
            f"❌ Error al enviar mensaje a Telegram: {response.status_code} - {response.text}"
        )


def enviar_imagen_telegram(
    ruta_imagen, caption="", bot_token=None, chat_id=None
):
    """Envía una imagen (gráfico PNG) con un pie de foto a Telegram."""
    token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
    cid = chat_id or os.getenv("TELEGRAM_CHAT_ID")

    if not token or not cid:
        print(
            "⚠️ Credenciales de Telegram no configuradas. Saltando envío de imagen."
        )
        return

    if not os.path.exists(ruta_imagen):
        print(f"❌ La imagen {ruta_imagen} no existe.")
        return

    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    payload = {"chat_id": cid, "caption": caption, "parse_mode": "HTML"}

    with open(ruta_imagen, "rb") as foto:
        files = {"photo": foto}
        response = requests.post(
            url, data=payload, files=files, timeout=15
        )

    if response.status_code == 200:
        print("📊 Gráfico enviado correctamente a Telegram.")
    else:
        print(
            f"❌ Error al enviar foto a Telegram: {response.status_code} - {response.text}"
        )


def dar_formato_resumen_omip(df):
    """Construye la plantilla del mensaje de texto formateado en HTML con los datos clave del DataFrame."""
    if df is None or df.empty:
        return "⚠️ No hay datos disponibles para OMIP."

    fecha = (
        df["Fecha_Extraccion"].iloc[0]
        if "Fecha_Extraccion" in df.columns
        else "N/A"
    )

    mensaje = "<b>⚡ Previsiones de Mercado Futuro (OMIP)</b>\n"
    mensaje += f"<i>Fecha: {fecha}</i>\n\n"
    mensaje += "<b>Resumen de Precios de Cierre:</b>\n"

    for _, fila in df.iterrows():
        contrato_raw = str(fila.iloc[0]).strip()

        # Extraer el nombre del contrato omitiendo prefijos
        if "Fixo MWh:" in contrato_raw:
            contrato = contrato_raw.split("Fixo MWh:")[1].strip()
        elif ":" in contrato_raw:
            contrato = contrato_raw.split(":")[-1].strip()
        else:
            contrato = contrato_raw

        # Limpiar residuos iniciales de '€/MWh'
        contrato = contrato.replace("€/MWh", "").strip()

        # Buscar el valor numérico recorriendo todas las columnas de la fila
        precio_val = "N/D"
        for val in fila.values[1:]:
            val_str = str(val).strip()
            if val_str == fecha or val_str.lower() == "nan":
                continue

            # Buscar patrones numéricos como 54.20 o 54,20 dentro de la celda
            match = re.search(r"(\d+[.,]\d+|\d+)", val_str)
            if match:
                precio_val = match.group(1).replace(",", ".")
                break

        mensaje += f"• <b>{contrato}:</b> {precio_val} €/MWh\n"

    mensaje += "\n📈 <i>Adjunto gráfico de la curva a futuro.</i>"
    return mensaje
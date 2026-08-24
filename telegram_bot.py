import os
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

    # Buscar automáticamente la columna de precio por palabra clave
    col_precio = None
    for col in df.columns:
        c_lower = str(col).lower()
        if any(
            k in c_lower
            for k in ["precio", "last", "settle", "cierre", "ultimo"]
        ):
            col_precio = col
            break

    for _, fila in df.iterrows():
        contrato_raw = str(fila.iloc[0]).strip()

        # Extraer el nombre legible del contrato (omite la cabecera 'ISIN Code: ...')
        if "Fixo MWh:" in contrato_raw:
            contrato = contrato_raw.split("Fixo MWh:")[1].strip()
        elif ":" in contrato_raw:
            contrato = contrato_raw.split(":")[-1].strip()
        else:
            contrato = contrato_raw

        # Seleccionar valor del precio
        if col_precio and pd.notnull(fila[col_precio]):
            precio_val = str(fila[col_precio]).strip()
        elif (
            "precio_limpio" in fila
            and pd.notnull(fila["precio_limpio"])
        ):
            precio_val = f"{float(fila['precio_limpio']):.2f}"
        else:
            precio_val = str(fila.iloc[1]).strip()

        mensaje += f"• <b>{contrato}:</b> {precio_val} €/MWh\n"

    mensaje += "\n📈 <i>Adjunto gráfico de la curva a futuro.</i>"
    return mensaje
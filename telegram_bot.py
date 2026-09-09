import os
import re
import sys
import pandas as pd
import requests


def _carpeta_base():
    """Carpeta donde está el script o el ejecutable."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def _cargar_config_local():
    """Lee telegram_config.txt junto al programa, sin publicar secretos."""
    ruta = os.path.join(_carpeta_base(), "telegram_config.txt")
    if not os.path.exists(ruta):
        return {}

    config = {}
    try:
        with open(ruta, "r", encoding="utf-8") as archivo:
            for linea in archivo:
                linea = linea.strip()
                if not linea or linea.startswith("#") or "=" not in linea:
                    continue
                clave, valor = linea.split("=", 1)
                config[clave.strip()] = valor.strip().strip('"').strip("'")
    except Exception as exc:
        print(f"⚠️ No se pudo leer telegram_config.txt: {exc}")
    return config


def _credenciales_telegram(bot_token=None, chat_id=None):
    """Obtiene credenciales: argumentos > variables de entorno > archivo local."""
    local = _cargar_config_local()
    token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN") or local.get("TELEGRAM_BOT_TOKEN")
    cid = chat_id or os.getenv("TELEGRAM_CHAT_ID") or local.get("TELEGRAM_CHAT_ID")
    return token, cid


def enviar_mensaje_telegram(mensaje, bot_token=None, chat_id=None):
    """Envía un mensaje de texto formateado en HTML a Telegram."""
    token, cid = _credenciales_telegram(bot_token, chat_id)

    if not token or not cid:
        print("⚠️ Credenciales de Telegram no configuradas. Saltando envío.")
        return False

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
        return True

    print(f"❌ Error al enviar mensaje a Telegram: {response.status_code} - {response.text}")
    return False


def enviar_imagen_telegram(ruta_imagen, caption="", bot_token=None, chat_id=None):
    """Envía una imagen (gráfico PNG) con un pie de foto a Telegram."""
    token, cid = _credenciales_telegram(bot_token, chat_id)

    if not token or not cid:
        print("⚠️ Credenciales de Telegram no configuradas. Saltando envío de imagen.")
        return False

    if not os.path.exists(ruta_imagen):
        print(f"❌ La imagen {ruta_imagen} no existe en la ruta: {ruta_imagen}")
        return False

    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    payload = {"chat_id": cid, "caption": caption, "parse_mode": "HTML"}

    try:
        with open(ruta_imagen, "rb") as foto:
            files = {"photo": foto}
            response = requests.post(url, data=payload, files=files, timeout=15)
    except requests.RequestException as exc:
        print(f"❌ Error de conexión con Telegram: {exc}")
        return False

    if response.status_code == 200:
        print("📊 Gráfico enviado correctamente a Telegram.")
        return True

    print(f"❌ Error al enviar foto a Telegram: {response.status_code} - {response.text}")
    return False


def dar_formato_resumen_omip(df):
    """Construye la plantilla del mensaje formateado omitiendo filas inválidas o nulas."""
    if df is None or df.empty:
        return "⚠️ No hay datos disponibles para OMIP."

    fecha = df["Fecha_Extraccion"].iloc[0] if "Fecha_Extraccion" in df.columns else "N/A"

    mensaje = "<b>⚡ Previsiones de Mercado Futuro (OMIP)</b>\n"
    mensaje += f"<i>Fecha: {fecha}</i>\n\n"
    mensaje += "<b>Resumen de Precios de Cierre:</b>\n"

    for i in range(len(df)):
        fila = df.iloc[i]
        contrato_raw = str(fila.iloc[0]).strip()

        if not contrato_raw or contrato_raw.lower() in ["nan", "none", "contract name"] or "Contract name" in contrato_raw:
            continue

        if "Fixo MWh:" in contrato_raw:
            contrato = contrato_raw.split("Fixo MWh:")[1].strip()
        elif ":" in contrato_raw:
            contrato = contrato_raw.split(":")[-1].strip()
        else:
            contrato = contrato_raw

        contrato = contrato.replace("€/MWh", "").strip()

        precio_val = None
        for j in range(1, len(fila)):
            val = fila.iloc[j]
            if pd.isnull(val):
                continue
            val_str = str(val).strip()
            if val_str in ["0", "0.0", "nan", "None", fecha]:
                continue

            match = re.search(r"(\d+[.,]\d+|\d+)", val_str)
            if match:
                val_float = float(match.group(1).replace(",", "."))
                if 0 < val_float < 1000:
                    precio_val = f"{val_float:.2f}"
                    break

        if precio_val is not None:
            mensaje += f"• <b>{contrato}:</b> {precio_val} €/MWh\n"

    mensaje += "\n📈 <i>Adjunto gráfico de la curva a futuro.</i>"
    return mensaje

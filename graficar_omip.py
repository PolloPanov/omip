import os
import re
import matplotlib.pyplot as plt
import pandas as pd


def extraer_precio_real(fila, df_columns):
    """Busca el precio únicamente en columnas con encabezados de liquidación/cierre."""
    cols_cierre = [col for col in df_columns if any(k in str(col).lower() for k in ["settlement", "cierre", "last", "precio", "unid", "siga", "1"])]
    indices_a_buscar = [df_columns.get_loc(c) for c in cols_cierre] if cols_cierre else list(range(1, len(fila)))
    for idx in indices_a_buscar:
        val = fila.iloc[idx]
        if pd.isnull(val):
            continue
        match = re.search(r"(\d+[.,]\d+|\d+)", str(val).strip())
        if match:
            try:
                val_float = float(match.group(1).replace(",", "."))
                if 15.0 <= val_float <= 250.0:
                    return val_float
            except ValueError:
                continue
    return None


def preparar_datos_grafico(df):
    contratos, precios = [], []
    if df is None or df.empty:
        return contratos, precios
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
        precio = extraer_precio_real(fila, df.columns)
        if precio is not None and contrato not in contratos:
            contratos.append(contrato)
            precios.append(precio)
    return contratos, precios


def generar_grafico_omip(df):
    """Genera el gráfico diario actual de la curva de 365 días."""
    if df is None or df.empty:
        print("❌ DataFrame vacío. No se puede generar gráfico.")
        return None
    contratos, precios = preparar_datos_grafico(df)
    if not precios:
        print("⚠️ No se encontraron precios válidos para graficar.")
        return None
    plt.figure(figsize=(15, 6))
    plt.plot(contratos, precios, marker="o", color="#0066cc", linewidth=2, markersize=5, label="Precio Liquidación (€/MWh)")
    for x, y in zip(contratos, precios):
        plt.annotate(f"{y:.2f}", (x, y), textcoords="offset points", xytext=(0, 6), ha="center", fontsize=7, weight="bold")
    plt.title("Curva de Precios Futuros OMIP (365 Días)", fontsize=13, pad=15)
    plt.xlabel("Vencimientos", fontsize=10)
    plt.ylabel("Precio (€/MWh)", fontsize=10)
    plt.xticks(rotation=45, ha="right", fontsize=7.5)
    plt.ylim(min(precios) - 5, max(precios) + 10)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    ruta_salida = os.path.abspath("curva_precios_omip.png")
    plt.savefig(ruta_salida, dpi=300)
    plt.close()
    print(f"✅ Gráfico filtrado correctamente en: {ruta_salida}")
    return ruta_salida


def _graficar_historico(historico, titulo, ruta_salida):
    """Grafica un histórico diario con una línea por contrato."""
    if historico is None or historico.empty:
        print("❌ No hay histórico para generar la gráfica.")
        return None
    datos = historico.copy()
    datos["fecha"] = pd.to_datetime(datos["fecha"], errors="coerce")
    datos["precio"] = pd.to_numeric(datos["precio"], errors="coerce")
    datos = datos.dropna(subset=["fecha", "precio"]).sort_values("fecha")
    if datos.empty:
        print("❌ No hay datos válidos en el histórico.")
        return None
    contratos = datos["contrato"].dropna().unique() if "contrato" in datos.columns else []
    plt.figure(figsize=(15, 7))
    if len(contratos):
        for contrato in contratos:
            serie = datos[datos["contrato"] == contrato].sort_values("fecha")
            if len(serie) >= 2:
                plt.plot(serie["fecha"], serie["precio"], marker="o", linewidth=1.8, markersize=3, label=str(contrato))
    else:
        plt.plot(datos["fecha"], datos["precio"], marker="o", linewidth=1.8, markersize=3)
    plt.title(titulo, fontsize=13, pad=15)
    plt.xlabel("Fecha", fontsize=10)
    plt.ylabel("Precio (€/MWh)", fontsize=10)
    plt.grid(True, linestyle="--", alpha=0.5)
    if len(contratos) and len(contratos) <= 20:
        plt.legend(fontsize=7, ncol=2)
    plt.tight_layout()
    os.makedirs(os.path.dirname(ruta_salida) or ".", exist_ok=True)
    plt.savefig(ruta_salida, dpi=300)
    plt.close()
    print(f"✅ Gráfica creada en: {os.path.abspath(ruta_salida)}")
    return os.path.abspath(ruta_salida)


def generar_grafico_30_dias(historico, ruta_salida="curva_precios_omip_30_dias.png"):
    """Genera la gráfica de los últimos 30 días disponibles."""
    if historico is None or historico.empty:
        print("❌ No hay histórico para generar la gráfica de 30 días.")
        return None
    datos = historico.copy()
    datos["fecha"] = pd.to_datetime(datos["fecha"], errors="coerce")
    datos = datos.dropna(subset=["fecha"]).sort_values("fecha")
    if datos.empty:
        return None
    fecha_max = datos["fecha"].max()
    fecha_min = fecha_max - pd.Timedelta(days=29)
    datos = datos[datos["fecha"].between(fecha_min, fecha_max)]
    return _graficar_historico(datos, "Evolución de Precios Futuros OMIP - Últimos 30 Días", ruta_salida)


def generar_grafico_mensual(historico, anio=None, mes=None, ruta_salida=None):
    """Genera la gráfica con los datos diarios de un mes."""
    if historico is None or historico.empty:
        print("❌ No hay histórico para generar la gráfica mensual.")
        return None
    datos = historico.copy()
    datos["fecha"] = pd.to_datetime(datos["fecha"], errors="coerce")
    datos = datos.dropna(subset=["fecha"]).sort_values("fecha")
    if datos.empty:
        return None
    if anio is None or mes is None:
        ultima_fecha = datos["fecha"].max()
        anio, mes = ultima_fecha.year, ultima_fecha.month
    anio, mes = int(anio), int(mes)
    datos = datos[(datos["fecha"].dt.year == anio) & (datos["fecha"].dt.month == mes)]
    if datos.empty:
        print(f"⚠️ No hay datos para {mes:02d}/{anio}.")
        return None
    nombres_meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    if ruta_salida is None:
        ruta_salida = os.path.join("graficas_mensuales", f"omip_{anio}_{mes:02d}.png")
    return _graficar_historico(datos, f"Evolución de Precios Futuros OMIP - {nombres_meses[mes - 1].capitalize()} {anio}", ruta_salida)

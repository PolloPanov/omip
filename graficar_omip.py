import os
import matplotlib.pyplot as plt
import pandas as pd


def generar_grafico_omip(df):
    """Genera un gráfico PNG con la curva de precios futuros de OMIP."""
    if df is None or df.empty:
        print("⚠️ No hay datos válidos para generar el gráfico.")
        return None

    df_plot = df.copy()

    col_contrato = df_plot.columns[0]

    # Extraer estrictamente una sola Series (la segunda columna)
    serie_raw = df_plot.iloc[:, 1].astype(str)

    # Limpiar formato y extraer números
    serie_limpia = (
        serie_raw.str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .str.extract(r"(\d+\.?\d*)")[0]
    )

    df_plot["precio_limpio"] = pd.to_numeric(serie_limpia, errors="coerce")
    df_plot = df_plot.dropna(subset=["precio_limpio"])

    if df_plot.empty:
        print("⚠️ No hay precios válidos tras la conversión.")
        return None

    # Configurar e imprimir gráfico
    plt.figure(figsize=(10, 5))
    plt.plot(
        df_plot[col_contrato],
        df_plot["precio_limpio"],
        marker="o",
        color="#1f77b4",
        linewidth=2,
    )

    plt.title("Curva de Precios Futuros de Electricidad (OMIP)", fontsize=14)
    plt.xlabel("Contrato", fontsize=10)
    plt.ylabel("Precio (€/MWh)", fontsize=10)
    plt.xticks(rotation=45, ha="right")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()

    ruta_salida = "curva_precios_omip.png"
    plt.savefig(ruta_salida, dpi=300)
    plt.close()

    print(f"📊 Gráfico generado con éxito: {ruta_salida}")
    return ruta_salida
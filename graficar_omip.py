import os
import matplotlib.pyplot as plt
import pandas as pd


def generar_grafico_omip(df):
    """Genera un gráfico PNG con la curva de precios futuros de OMIP."""
    if df is None or df.empty:
        print("⚠️ No hay datos válidos para generar el gráfico.")
        return None

    df_plot = df.copy()

    # Identificar columnas (primera: contrato/producto, segunda: precio)
    col_contrato = df_plot.columns[0]
    col_precio = df_plot.columns[1]

    # Convertir columna de precio a formato numérico (limpia comas y puntos)
    df_plot[col_precio] = (
        df_plot[col_precio]
        .astype(str)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
    )
    df_plot[col_precio] = pd.to_numeric(df_plot[col_precio], errors="coerce")

    # Eliminar posibles filas sin valores numéricos
    df_plot = df_plot.dropna(subset=[col_precio])

    if df_plot.empty:
        print("⚠️ No hay precios válidos tras la conversión.")
        return None

    # Configuración e impresión del gráfico
    plt.figure(figsize=(10, 5))
    plt.plot(
        df_plot[col_contrato],
        df_plot[col_precio],
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

    # Guardar imagen en disco
    ruta_salida = "curva_precios_omip.png"
    plt.savefig(ruta_salida, dpi=300)
    plt.close()

    print(f"📊 Gráfico generado con éxito: {ruta_salida}")
    return ruta_salida
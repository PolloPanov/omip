import datetime
import os
import matplotlib.pyplot as plt
import pandas as pd


def generar_grafico_omip(df, nombre_archivo=None):
    """Genera un gráfico de línea con la curva de precios de futuros de OMIP

    y lo guarda como imagen PNG.
    """
    if df.empty:
        print("El DataFrame está vacío. No se puede generar el gráfico.")
        return None

    if nombre_archivo is None:
        fecha_str = datetime.date.today().strftime("%Y%m%d")
        nombre_archivo = f"curva_omip_{fecha_str}.png"

    # 1. Identificar columnas clave (Ajustar según nombres de columna en tu DataFrame)
    col_contrato = None
    col_precio = None

    for col in df.columns:
        c_lower = col.lower()
        if "contract" in c_lower or "contrato" in c_lower or "producto" in c_lower:
            col_contrato = col
        if (
            "settlement" in c_lower
            or "cierre" in c_lower
            or "precio" in c_lower
            or "último" in c_lower
        ):
            col_precio = col

    # Fallback si no detecta por nombre: usar la 1ª columna como contrato y la 2ª como precio
    if not col_contrato:
        col_contrato = df.columns[0]
    if not col_precio:
        col_precio = df.columns[1]

    # 2. Limpieza de datos para el gráfico
    df_plot = df.copy()

    # Si el precio sigue siendo tipo texto/if df_plot[col_precio].dtype == "O":
        # Convierte automáticamente a número reemplazando comas por puntos
df_plot[col_precio] = df_plot[col_precio].astype(str).str.replace(',', '.')
# Convertir coma decimal a punto y transformar a número
df_plot[col_precio] = df_plot[col_precio].astype(str).str.replace(',', '.')
df_plot[col_precio] = pd.to_numeric(df_plot[col_precio], errors='coerce')
            df_plot[col_precio]
            .astype(str)
            .str.replace(".", "", regex=False)
            .str.replace(",", ".", regex=False)
        )
        df_plot[col_precio] = pd.to_numeric(
            df_plot[col_precio], errors="coerce"
        )

    # Eliminar posibles filas sin precio
    df_plot = df_plot.dropna(subset=[col_precio])

    # Truncar nombres de contrato si son muy largos para mejorar la lectura en el eje X
    df_plot["Contrato_Corto"] = (
        df_plot[col_contrato].astype(str).str.split(":").str[0].str.strip()
    )

    x = df_plot["Contrato_Corto"]
    y = df_plot[col_precio]

    # 3. Configuración del diseño del gráfico con Matplotlib
    plt.figure(figsize=(10, 6), dpi=300)
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")

    # Dibujar la línea de la curva y los puntos de datos
    plt.plot(
        x,
        y,
        marker="o",
        color="#1f77b4",
        linewidth=2.5,
        markersize=8,
        label="Precio de Cierre (€/MWh)",
    )

    # Añadir etiquetas con el valor numérico en cada punto del gráfico
    for i, (txt_x, txt_y) in enumerate(zip(x, y)):
        plt.annotate(
            f"{txt_y:.2f} €",
            (i, txt_y),
            textcoords="offset points",
            xytext=(0, 10),
            ha="center",
            fontsize=9,
            fontweight="bold",
            color="#333333",
        )

    # Personalización de títulos y ejes
    fecha_hoy = datetime.date.today().strftime("%d/%m/%Y")
    plt.title(
        f"Curva de Precios de Futuros de Electricidad - OMIP ({fecha_hoy})",
        fontsize=14,
        fontweight="bold",
        pad=20,
    )
    plt.xlabel("Contratos a Futuro", fontsize=11, labelpad=10)
    plt.ylabel("Precio (€/MWh)", fontsize=11, labelpad=10)

    plt.xticks(rotation=30, ha="right", fontsize=9)
    plt.yticks(fontsize=9)

    # Ajustar márgenes para que todo quepa perfectamente
    plt.tight_layout()

    # 4. Guardar la imagen
    plt.savefig(nombre_archivo, format="png")
    plt.close()

    print(f"📈 Gráfico generado y guardado como: {nombre_archivo}")
    return nombre_archivo


# --- EJEMPLO DE USO CON TU SCRIPT PRINCIPAL ---
if __name__ == "__main__":
    from extraer_omip import obtener_precios_omip

    # Extraer los datos
    df_omip = obtener_precios_omip()

    # Generar el gráfico
    generar_grafico_omip(df_omip)
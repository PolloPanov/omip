import os
import re
import matplotlib.pyplot as plt
import pandas as pd


def generar_grafico_omip(df):
    """Genera una imagen PNG con la curva de precios futuros de OMIP a 365 días."""
    if df is None or df.empty:
        print("❌ DataFrame vacío. No se puede generar el gráfico.")
        return None

    contratos = []
    precios = []

    # Procesar filas para extraer contratos válidos y precios flotantes
    for i in range(len(df)):
        fila = df.iloc[i]
        contrato_raw = str(fila.iloc[0]).strip()

        # Descartar cabeceras, nulos y texto basura
        if (
            not contrato_raw
            or contrato_raw.lower() in ["nan", "none", "contract name"]
            or "Contract name" in contrato_raw
        ):
            continue

        # Limpiar el nombre del contrato
        if "Fixo MWh:" in contrato_raw:
            contrato = contrato_raw.split("Fixo MWh:")[1].strip()
        elif ":" in contrato_raw:
            contrato = contrato_raw.split(":")[-1].strip()
        else:
            contrato = contrato_raw

        contrato = contrato.replace("€/MWh", "").strip()

        # Extraer el precio numérico de las columnas siguientes
        precio_num = None
        for j in range(1, len(fila)):
            val = fila.iloc[j]
            if pd.isnull(val):
                continue
            val_str = str(val).strip()
            if val_str in ["0", "0.0", "nan", "None"]:
                continue

            match = re.search(r"(\d+[.,]\d+|\d+)", val_str)
            if match:
                val_float = float(match.group(1).replace(",", "."))
                # Filtro de rango válido de precios €/MWh
                if 0 < val_float < 1000:
                    precio_num = val_float
                    break

        if precio_num is not None:
            contratos.append(contrato)
            precios.append(precio_num)

    if not precios:
        print("⚠️ No se encontraron precios válidos para graficar.")
        return None

    # Ajustar dimensiones del gráfico para el volumen de 365 días
    plt.figure(figsize=(15, 6))
    plt.plot(
        contratos,
        precios,
        marker="o",
        color="#0066cc",
        linewidth=2,
        markersize=6,
        label="Cierre (€/MWh)",
    )

    # Anotaciones de valor sobre los puntos de la curva
    for idx, (x, y) in enumerate(zip(contratos, precios)):
        plt.annotate(
            f"{y:.2f}",
            (x, y),
            textcoords="offset points",
            xytext=(0, 7),
            ha="center",
            fontsize=7.5,
            weight="bold",
        )

    plt.title("Curva de Precios Futuros OMIP (365 Días)", fontsize=14, pad=15)
    plt.xlabel("Contratos (Días / Meses / Trimestres / Años)", fontsize=10)
    plt.ylabel("Precio (€/MWh)", fontsize=10)
    plt.xticks(rotation=45, ha="right", fontsize=8)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()

    # Guardar en la raíz con ruta absoluta
    ruta_salida = os.path.abspath("curva_precios_omip.png")
    plt.savefig(ruta_salida, dpi=300)
    plt.close()

    print(f"✅ Gráfico de 365 días generado con éxito en: {ruta_salida}")
    return ruta_salida
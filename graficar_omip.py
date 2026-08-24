import os
import re
import matplotlib.pyplot as plt
import pandas as pd


def generar_grafico_omip(df):
    """Genera una imagen PNG con la curva de precios de los contratos OMIP."""
    if df is None or df.empty:
        print("❌ DataFrame vacío. No se puede generar gráfico.")
        return None

    contratos = []
    precios = []

    for i in range(len(df)):
        fila = df.iloc[i]
        contrato_raw = str(fila.iloc[0]).strip()

        # Descartar filas inválidas o cabeceras
        if (
            not contrato_raw
            or contrato_raw.lower() in ["nan", "none", "contract name"]
            or "Contract name" in contrato_raw
        ):
            continue

        # Limpiar nombre del contrato
        if "Fixo MWh:" in contrato_raw:
            contrato = contrato_raw.split("Fixo MWh:")[1].strip()
        elif ":" in contrato_raw:
            contrato = contrato_raw.split(":")[-1].strip()
        else:
            contrato = contrato_raw

        contrato = contrato.replace("€/MWh", "").strip()

        # Extraer precio numérico
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
                if val_float > 0 and val_float < 1000:
                    precio_num = val_float
                    break

        if precio_num is not None:
            contratos.append(contrato)
            precios.append(precio_num)

    if not precios:
        print("⚠️ No hay precios válidos para graficar.")
        return None

    # Trazar gráfico
    plt.figure(figsize=(10, 5))
    plt.plot(
        contratos,
        precios,
        marker="o",
        color="#1f77b4",
        linewidth=2.5,
        markersize=8,
    )

    for idx, (x, y) in enumerate(zip(contratos, precios)):
        plt.annotate(
            f"{y:.2f} €",
            (x, y),
            textcoords="offset points",
            xytext=(0, 10),
            ha="center",
            fontsize=9,
            weight="bold",
        )

    plt.title("Curva de Precios Futuros OMIP", fontsize=14, pad=15)
    plt.xlabel("Contrato", fontsize=11)
    plt.ylabel("Precio (€/MWh)", fontsize=11)
    plt.xticks(rotation=25, ha="right")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()

    ruta_salida = os.path.abspath("curva_precios_omip.png")
    plt.savefig(ruta_salida, dpi=300)
    plt.close()

    print(f"✅ Gráfico generado correctamente en: {ruta_salida}")
    return ruta_salida
import os
import re
import matplotlib.pyplot as plt
import pandas as pd


def extraer_precio_real(fila, df_columns):
    """Busca el precio únicamente en columnas con encabezados de liquidación/cierre."""
    # Buscar primero si existe una columna explícita de precio/cierre
    cols_cierre = [
        col
        for col in df_columns
        if any(
            k in str(col).lower()
            for k in [
                "settlement",
                "cierre",
                "last",
                "precio",
                "unid",
                "siga",
                "1",
            ]
        )
    ]

    indices_a_buscar = (
        [df_columns.get_loc(c) for c in cols_cierre]
        if cols_cierre
        else list(range(1, len(fila)))
    )

    for idx in indices_a_buscar:
        val = fila.iloc[idx]
        if pd.isnull(val):
            continue
        val_str = str(val).strip()

        # Extraer float
        match = re.search(r"(\d+[.,]\d+|\d+)", val_str)
        if match:
            try:
                val_float = float(match.group(1).replace(",", "."))
                # Filtro acotado de precios lógicos en OMIP (15 €/MWh - 250 €/MWh)
                if 15.0 <= val_float <= 250.0:
                    return val_float
            except ValueError:
                continue
    return None


def generar_grafico_omip(df):
    """Genera un gráfico filtrado y limpio para la curva de 365 días."""
    if df is None or df.empty:
        print("❌ DataFrame vacío. No se puede generar gráfico.")
        return None

    contratos = []
    precios = []

    for i in range(len(df)):
        fila = df.iloc[i]
        contrato_raw = str(fila.iloc[0]).strip()

        # Filtrar valores nulos o encabezados repetidos
        if (
            not contrato_raw
            or contrato_raw.lower() in ["nan", "none", "contract name"]
            or "Contract name" in contrato_raw
        ):
            continue

        # Limpiar etiqueta del contrato
        if "Fixo MWh:" in contrato_raw:
            contrato = contrato_raw.split("Fixo MWh:")[1].strip()
        elif ":" in contrato_raw:
            contrato = contrato_raw.split(":")[-1].strip()
        else:
            contrato = contrato_raw

        contrato = contrato.replace("€/MWh", "").strip()

        # Extraer precio verificado
        precio = extraer_precio_real(fila, df.columns)

        if precio is not None and contrato not in contratos:
            contratos.append(contrato)
            precios.append(precio)

    if not precios:
        print("⚠️ No se encontraron precios válidos para graficar.")
        return None

    # Trazar curva acotada y coherente
    plt.figure(figsize=(15, 6))
    plt.plot(
        contratos,
        precios,
        marker="o",
        color="#0066cc",
        linewidth=2,
        markersize=5,
        label="Precio Liquidación (€/MWh)",
    )

    for x, y in zip(contratos, precios):
        plt.annotate(
            f"{y:.2f}",
            (x, y),
            textcoords="offset points",
            xytext=(0, 6),
            ha="center",
            fontsize=7,
            weight="bold",
        )

    plt.title("Curva de Precios Futuros OMIP (365 Días)", fontsize=13, pad=15)
    plt.xlabel("Vencimientos", fontsize=10)
    plt.ylabel("Precio (€/MWh)", fontsize=10)
    plt.xticks(rotation=45, ha="right", fontsize=7.5)
    plt.ylim(
        min(precios) - 5, max(precios) + 10
    )  # Escala ajustada automáticamente
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()

    ruta_salida = os.path.abspath("curva_precios_omip.png")
    plt.savefig(ruta_salida, dpi=300)
    plt.close()

    print(f"✅ Gráfico filtrado correctamente en: {ruta_salida}")
    return ruta_salida
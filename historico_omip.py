import argparse
import glob
import os
import re
from datetime import date, timedelta

import matplotlib.pyplot as plt
import pandas as pd

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def extraer_historico():
    registros = []
    for archivo in sorted(glob.glob("omip_futuros_365d_*.csv")):
        try:
            df = pd.read_csv(archivo, header=1, encoding="utf-8-sig")
        except Exception as exc:
            print(f"⚠️ No se pudo leer {archivo}: {exc}")
            continue
        if df.empty:
            continue
        fecha_col = next((c for c in df.columns if str(c).strip() == "Fecha_Extraccion"), None)
        contrato_col = next((c for c in df.columns if str(c).strip() == "Contract name"), None)
        precio_col = next((c for c in df.columns if str(c).strip().startswith("D (€/MWh)")), None)
        if not all([fecha_col, contrato_col, precio_col]):
            print(f"⚠️ Estructura no reconocida en {archivo}; se omite.")
            continue
        tmp = df[[fecha_col, contrato_col, precio_col]].copy()
        tmp.columns = ["fecha", "contrato_raw", "precio"]
        tmp["fecha"] = pd.to_datetime(tmp["fecha"], errors="coerce")
        tmp["precio"] = pd.to_numeric(tmp["precio"], errors="coerce")
        tmp = tmp.dropna(subset=["fecha", "precio"])

        def limpiar_contrato(valor):
            texto = str(valor).strip()
            if not texto or texto.lower() in {"nan", "none", "contract name"}:
                return None
            match = re.search(r"FTB\s+(.+)$", texto)
            return match.group(1).strip() if match else texto

        tmp["contrato"] = tmp["contrato_raw"].map(limpiar_contrato)
        tmp = tmp.dropna(subset=["contrato"])
        registros.append(tmp[["fecha", "contrato", "precio"]])

    if not registros:
        return pd.DataFrame(columns=["fecha", "contrato", "precio"])
    historico = pd.concat(registros, ignore_index=True)
    historico = historico.drop_duplicates(subset=["fecha", "contrato"], keep="last")
    return historico.sort_values(["fecha", "contrato"]).reset_index(drop=True)


def generar_grafica(datos, titulo, ruta):
    if datos.empty:
        print(f"⚠️ No hay datos para generar {ruta}.")
        return False
    os.makedirs(os.path.dirname(ruta) or ".", exist_ok=True)
    plt.figure(figsize=(16, 8))
    contratos = datos["contrato"].dropna().unique()
    for contrato in contratos:
        serie = datos[datos["contrato"] == contrato].sort_values("fecha")
        if len(serie) >= 2:
            plt.plot(serie["fecha"], serie["precio"], marker="o", markersize=2.5, linewidth=1.2, label=str(contrato))
    plt.title(titulo, fontsize=14, pad=15)
    plt.xlabel("Fecha", fontsize=10)
    plt.ylabel("Precio (€/MWh)", fontsize=10)
    plt.grid(True, linestyle="--", alpha=0.5)
    if len(contratos) <= 20:
        plt.legend(fontsize=7, ncol=2)
    plt.tight_layout()
    plt.savefig(ruta, dpi=300)
    plt.close()
    print(f"✅ Gráfica creada: {ruta}")
    return True


def generar_30_dias(historico, salida="graficas_historicas/omip_ultimos_30_dias.png"):
    if historico.empty:
        return False
    fecha_max = historico["fecha"].max()
    fecha_min = fecha_max - pd.Timedelta(days=29)
    datos = historico[historico["fecha"].between(fecha_min, fecha_max)]
    return generar_grafica(datos, "Evolución de Precios Futuros OMIP - Últimos 30 Días", salida)


def generar_mes(historico, anio, mes):
    datos = historico[(historico["fecha"].dt.year == anio) & (historico["fecha"].dt.month == mes)]
    ruta = os.path.join("graficas_historicas", f"omip_{anio}_{mes:02d}.png")
    return generar_grafica(datos, f"Evolución de Precios Futuros OMIP - {MESES[mes - 1].capitalize()} {anio}", ruta)


def main():
    parser = argparse.ArgumentParser(description="Genera gráficas históricas OMIP a partir de los CSV diarios.")
    parser.add_argument("--30-dias", dest="ultimos_30", action="store_true", help="Genera la gráfica de los últimos 30 días disponibles.")
    parser.add_argument("--mes", nargs=2, type=int, metavar=("ANIO", "MES"), help="Genera un mes concreto, por ejemplo --mes 2026 9.")
    parser.add_argument("--mensual-si-corresponde", action="store_true", help="Genera el mes natural anterior cuando hoy es día 1.")
    args = parser.parse_args()
    historico = extraer_historico()
    if historico.empty:
        print("❌ No se encontraron datos históricos en los CSV diarios.")
        return 1
    if args.ultimos_30:
        generar_30_dias(historico)
    if args.mes:
        anio, mes = args.mes
        if not 1 <= mes <= 12:
            parser.error("El mes debe estar entre 1 y 12.")
        generar_mes(historico, anio, mes)
    if args.mensual_si_corresponde and date.today().day == 1:
        fecha_anterior = date.today().replace(day=1) - timedelta(days=1)
        generar_mes(historico, fecha_anterior.year, fecha_anterior.month)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

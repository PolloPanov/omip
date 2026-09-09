import argparse
import glob
import os
import re

import matplotlib.pyplot as plt
import pandas as pd
import requests
from bs4 import BeautifulSoup

from telegram_bot import enviar_imagen_telegram


OMIP_MERCADO_HOY_URL = (
    "https://www.omip.pt/en/plazo-hoy"
)


def obtener_spel_base_hoy():
    """
    Obtiene automáticamente de la web oficial de OMIP
    el precio actual de SPEL BASE.

    Ejemplo:
        SPEL BASE €145.21

    Devuelve:
        float -> 145.21
    """

    try:
        respuesta = requests.get(
            OMIP_MERCADO_HOY_URL,
            timeout=20,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/131.0 Safari/537.36"
                )
            },
        )

        respuesta.raise_for_status()

    except requests.RequestException as exc:
        raise RuntimeError(
            "No se pudo conectar con la web de OMIP "
            "para obtener el SPEL BASE."
        ) from exc

    try:
        soup = BeautifulSoup(
            respuesta.text,
            "html.parser",
        )

        # Convertimos toda la página a texto continuo.
        # Esto permite encontrar el dato aunque OMIP
        # cambie ligeramente la estructura HTML.
        texto = soup.get_text(
            " ",
            strip=True,
        )

        # Ejemplo que queremos detectar:
        #
        # SPEL BASE €145.21
        #
        # También admite:
        # SPEL BASE 145.21
        # SPEL BASE € 145.21
        # SPEL BASE €145,21
        patron = re.compile(
            r"SPEL\s+BASE\s*"
            r"(?:€\s*)?"
            r"([0-9]+(?:[.,][0-9]+)?)",
            re.IGNORECASE,
        )

        coincidencia = patron.search(
            texto
        )

        if not coincidencia:
            raise RuntimeError(
                "No se encontró el precio SPEL BASE "
                "en la página de OMIP."
            )

        valor_texto = (
            coincidencia.group(1)
            .replace(",", ".")
        )

        precio = float(
            valor_texto
        )

        if precio <= 0:
            raise RuntimeError(
                f"El precio SPEL BASE obtenido no es válido: "
                f"{precio}"
            )

        print(
            f"✅ SPEL BASE OMIP de hoy: "
            f"{precio:.2f} €/MWh"
        )

        return precio

    except (ValueError, AttributeError) as exc:
        raise RuntimeError(
            "No se pudo interpretar correctamente "
            "el precio SPEL BASE de OMIP."
        ) from exc


def extraer_historico():
    registros = []

    archivos = sorted(
        glob.glob(
            "omip_futuros_365d_*.csv"
        )
    )

    for archivo in archivos:

        try:
            df = pd.read_csv(
                archivo,
                header=1,
                encoding="utf-8-sig",
            )

        except Exception as exc:
            print(
                f"⚠️ No se pudo leer {archivo}: {exc}"
            )
            continue

        if df.empty:
            continue

        nombre = os.path.basename(
            archivo
        )

        match_fecha = re.search(
            r"omip_futuros_365d_(\d{8})\.csv$",
            nombre,
            re.IGNORECASE,
        )

        fecha_extraccion = pd.NaT

        if match_fecha:
            fecha_extraccion = pd.to_datetime(
                match_fecha.group(1),
                format="%Y%m%d",
                errors="coerce",
            )

        contrato_col = next(
            (
                c
                for c in df.columns
                if str(c).strip()
                == "Contract name"
            ),
            None,
        )

        precio_col = next(
            (
                c
                for c in df.columns
                if str(c).strip().startswith(
                    "D (€/MWh)"
                )
            ),
            None,
        )

        if (
            contrato_col is None
            or precio_col is None
        ):
            print(
                f"⚠️ Estructura no reconocida en "
                f"{archivo}; se omite."
            )
            continue

        tmp = df[
            [
                contrato_col,
                precio_col,
            ]
        ].copy()

        tmp.columns = [
            "contrato_raw",
            "precio",
        ]

        tmp["fecha"] = (
            fecha_extraccion
        )

        tmp["precio"] = pd.to_numeric(
            tmp["precio"],
            errors="coerce",
        )

        def limpiar_contrato(valor):

            texto = str(valor).strip()

            if (
                not texto
                or texto.lower()
                in {
                    "nan",
                    "none",
                    "contract name",
                }
            ):
                return None

            match = re.search(
                r"FTB\s+(.+)$",
                texto,
                re.IGNORECASE,
            )

            if match:
                return match.group(1).strip()

            return texto

        tmp["contrato"] = (
            tmp["contrato_raw"].map(
                limpiar_contrato
            )
        )

        tmp = tmp.dropna(
            subset=[
                "fecha",
                "precio",
                "contrato",
            ]
        )

        registros.append(
            tmp[
                [
                    "fecha",
                    "contrato",
                    "precio",
                ]
            ]
        )

    if not registros:
        return pd.DataFrame(
            columns=[
                "fecha",
                "contrato",
                "precio",
            ]
        )

    historico = pd.concat(
        registros,
        ignore_index=True,
    )

    historico = historico.drop_duplicates(
        subset=[
            "fecha",
            "contrato",
        ],
        keep="last",
    )

    return historico.sort_values(
        [
            "fecha",
            "contrato",
        ]
    ).reset_index(
        drop=True
    )


def filtrar_trimestrales(datos):
    """
    Devuelve únicamente contratos trimestrales:

        Q1-27
        Q2-27
        Q3-27
        Q4-27
        etc.
    """

    if datos.empty:
        return datos.copy()

    resultado = datos[
        datos["contrato"].str.match(
            r"^Q[1-4]-\d{2}$",
            na=False,
        )
    ].copy()

    return resultado


def generar_grafica(
    datos,
    titulo,
    ruta,
    contrato_destacado=None,
    precio_spel_base=None,
):
    """
    Genera la gráfica histórica.

    Si precio_spel_base está disponible,
    añade una línea horizontal a toda la gráfica
    representando el SPEL BASE publicado hoy por OMIP.
    """

    if datos.empty:
        print(
            f"⚠️ No hay datos para generar {ruta}."
        )
        return False

    os.makedirs(
        os.path.dirname(ruta) or ".",
        exist_ok=True,
    )

    plt.figure(
        figsize=(15, 8)
    )

    if contrato_destacado:

        datos = datos[
            datos["contrato"]
            == contrato_destacado
        ].copy()

        if datos.empty:
            print(
                f"⚠️ No hay datos históricos para "
                f"{contrato_destacado}."
            )

            plt.close()

            return False

    contratos = sorted(
        datos["contrato"]
        .dropna()
        .unique()
    )

    for contrato in contratos:

        serie = datos[
            datos["contrato"] == contrato
        ].sort_values(
            "fecha"
        )

        if len(serie) < 2:
            continue

        plt.plot(
            serie["fecha"],
            serie["precio"],
            marker="o",
            markersize=3,
            linewidth=1.8,
            label=str(contrato),
        )

        ultimo = serie.iloc[-1]

        plt.annotate(
            f"{ultimo['precio']:.2f}",
            (
                ultimo["fecha"],
                ultimo["precio"],
            ),
            xytext=(6, 5),
            textcoords="offset points",
            fontsize=8,
        )

    ax = plt.gca()

    # ==========================================================
    # LÍNEA SPEL BASE DE HOY
    # ==========================================================

    if precio_spel_base is not None:

        ax.axhline(
            y=precio_spel_base,
            linestyle="--",
            linewidth=2.2,
            label=(
                "OMIP HOY · SPEL BASE "
                f"{precio_spel_base:.2f} €/MWh"
            ),
        )

    # ==========================================================
    # TÍTULO Y EJES
    # ==========================================================

    plt.title(
        titulo,
        fontsize=16,
        fontweight="bold",
        pad=18,
    )

    plt.xlabel(
        "Fecha de la predicción",
        fontsize=10,
    )

    plt.ylabel(
        "Precio previsto (€/MWh)",
        fontsize=10,
    )

    plt.grid(
        axis="y",
        linestyle="--",
        alpha=0.35,
    )

    ax.spines[
        "top"
    ].set_visible(False)

    ax.spines[
        "right"
    ].set_visible(False)

    # Mostramos la leyenda cuando:
    # - hay varios contratos, o
    # - tenemos la línea SPEL BASE.
    if (
        len(contratos) > 1
        or precio_spel_base is not None
    ):
        plt.legend(
            fontsize=8,
            ncol=2,
            loc="upper left",
        )

    plt.figtext(
        0.5,
        0.01,
        (
            "Evolución desde las predicciones "
            "más antiguas hasta las más recientes"
        ),
        ha="center",
        fontsize=9,
    )

    plt.tight_layout(
        rect=(
            0,
            0.03,
            1,
            1,
        )
    )

    plt.savefig(
        ruta,
        dpi=300,
        bbox_inches="tight",
        facecolor="white",
    )

    plt.close()

    print(
        f"✅ Gráfica creada: {ruta}"
    )

    return True


def generar_30_dias(
    historico,
    enviar_telegram=True,
):
    if historico.empty:
        return False

    historico = filtrar_trimestrales(
        historico
    )

    if historico.empty:
        print(
            "⚠️ No hay contratos trimestrales."
        )
        return False

    fecha_max = historico[
        "fecha"
    ].max()

    fecha_min = (
        fecha_max
        - pd.Timedelta(
            days=29
        )
    )

    datos = historico[
        historico["fecha"].between(
            fecha_min,
            fecha_max,
        )
    ].copy()

    # ==========================================================
    # OBTENER SPEL BASE DE HOY
    # ==========================================================

    try:
        precio_spel_base = (
            obtener_spel_base_hoy()
        )

    except Exception as exc:

        print(
            f"⚠️ {exc}"
        )

        print(
            "⚠️ Se generará la gráfica "
            "sin la línea SPEL BASE."
        )

        precio_spel_base = None

    ruta = os.path.join(
        "graficas_historicas",
        "omip_ultimos_30_dias_trimestral.png",
    )

    creada = generar_grafica(
        datos,
        (
            "Evolución de Precios Futuros OMIP "
            "- Últimos 30 Días"
        ),
        ruta,
        precio_spel_base=precio_spel_base,
    )

    if not creada:
        return False

    if enviar_telegram:

        if precio_spel_base is not None:

            caption = (
                "📈 <i>Evolución de Precios "
                "Futuros OMIP</i>\n"
                "Últimos 30 días · "
                "Contratos trimestrales\n"
                f"📌 SPEL BASE hoy: "
                f"{precio_spel_base:.2f} €/MWh"
            )

        else:

            caption = (
                "📈 <i>Evolución de Precios "
                "Futuros OMIP</i>\n"
                "Últimos 30 días · "
                "Contratos trimestrales"
            )

        enviado = enviar_imagen_telegram(
            ruta,
            caption=caption,
        )

        if not enviado:
            return False

    return True


def generar_trimestre(
    historico,
    anio,
    trimestre,
    enviar_telegram=True,
):
    if trimestre not in (
        1,
        2,
        3,
        4,
    ):
        raise ValueError(
            "El trimestre debe ser 1, 2, 3 o 4."
        )

    if anio < 2000 or anio > 2100:
        raise ValueError(
            "El año no es válido."
        )

    codigo_contrato = (
        f"Q{trimestre}-"
        f"{str(anio)[-2:]}"
    )

    datos = filtrar_trimestrales(
        historico
    )

    datos = datos[
        datos["contrato"]
        == codigo_contrato
    ].copy()

    if datos.empty:
        print(
            f"⚠️ No hay datos históricos para "
            f"{codigo_contrato}."
        )
        return False

    datos = datos.sort_values(
        "fecha"
    )

    # ==========================================================
    # OBTENER SPEL BASE DE HOY
    # ==========================================================

    try:
        precio_spel_base = (
            obtener_spel_base_hoy()
        )

    except Exception as exc:

        print(
            f"⚠️ {exc}"
        )

        print(
            "⚠️ Se generará la gráfica "
            "sin la línea SPEL BASE."
        )

        precio_spel_base = None

    ruta = os.path.join(
        "graficas_historicas",
        f"omip_{codigo_contrato}.png",
    )

    titulo = (
        "Evolución del precio futuro OMIP - "
        f"{codigo_contrato}"
    )

    creada = generar_grafica(
        datos,
        titulo,
        ruta,
        contrato_destacado=codigo_contrato,
        precio_spel_base=precio_spel_base,
    )

    if not creada:
        return False

    if enviar_telegram:

        if precio_spel_base is not None:

            caption = (
                "📊 <i>Evolución del precio "
                "futuro OMIP</i>\n"
                f"Contrato {codigo_contrato}\n"
                f"📌 SPEL BASE hoy: "
                f"{precio_spel_base:.2f} €/MWh"
            )

        else:

            caption = (
                "📊 <i>Evolución del precio "
                "futuro OMIP</i>\n"
                f"Contrato {codigo_contrato}"
            )

        enviado = enviar_imagen_telegram(
            ruta,
            caption=caption,
        )

        if not enviado:
            return False

    return True


def main():

    parser = argparse.ArgumentParser(
        description=(
            "Genera gráficas históricas "
            "trimestrales OMIP."
        )
    )

    parser.add_argument(
        "--30-dias",
        dest="ultimos_30",
        action="store_true",
        help=(
            "Genera y envía la gráfica "
            "trimestral de los últimos "
            "30 días."
        ),
    )

    parser.add_argument(
        "--trimestre",
        nargs=2,
        type=int,
        metavar=(
            "ANIO",
            "TRIMESTRE",
        ),
        help=(
            "Genera un trimestre concreto. "
            "Ejemplo: --trimestre 2027 1"
        ),
    )

    args = parser.parse_args()

    historico = extraer_historico()

    if historico.empty:

        print(
            "❌ No se encontraron datos "
            "históricos en los CSV diarios."
        )

        return 1

    if args.ultimos_30:

        correcto = generar_30_dias(
            historico
        )

        return (
            0
            if correcto
            else 1
        )

    if args.trimestre:

        anio, trimestre = args.trimestre

        correcto = generar_trimestre(
            historico,
            anio,
            trimestre,
        )

        return (
            0
            if correcto
            else 1
        )

    parser.print_help()

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )

import os
import requests
import xml.etree.ElementTree as ET
import configparser
import zlib


# ===========================
# 🔹 LEER CONFIG.INI
# ===========================
config = configparser.ConfigParser()
config.read("config.ini")

try:
    URL_XML = config["UPDATE"]["xml_url"]
    DOWNLOAD_PATH = config["UPDATE"].get("download_path", "./")
except:
    raise Exception("❌ ERROR: Falta sección [UPDATE] en config.ini")


# Crear carpeta destino si no existe
if not os.path.exists(DOWNLOAD_PATH):
    os.makedirs(DOWNLOAD_PATH)


# ===========================
# 🔹 DESCARGAR XML
# ===========================
def descargar_xml(url=URL_XML, nombre="files.xml"):
    ruta = os.path.join(DOWNLOAD_PATH, nombre)

    r = requests.get(url, timeout=10)
    with open(ruta, "wb") as f:
        f.write(r.content)

    return ruta


# ===========================
# 🔹 PARSEAR XML → (NAME, URL, CRC)
# ===========================
def leer_xml(nombre_xml):
    tree = ET.parse(nombre_xml)
    root = tree.getroot()

    archivos = []
    for file in root.findall("file"):
        nombre = file.get("name")
        enlace = file.find("link").text
        crc    = file.get("crc", None)
        archivos.append((nombre, enlace, crc))

    return archivos


# ===========================
# 🔹 CALCULAR CRC32
# ===========================
def calcular_crc(path_file):
    if not os.path.exists(path_file):
        return None

    with open(path_file, "rb") as f:
        data = f.read()
        crc = zlib.crc32(data) & 0xFFFFFFFF
        return format(crc, "08X")  # Upper HEX como XML


# ===========================
# 🔹 DESCARGA CON RETRY + VALIDACIÓN CRC
# ===========================
def descargar_archivo(nombre, url, crc_esperado):
    ruta_final = os.path.join(DOWNLOAD_PATH, nombre)
    carpeta = os.path.dirname(ruta_final)

    if carpeta not in ("", ".") and not os.path.exists(carpeta):
        os.makedirs(carpeta)

    # Intentos para validar CRC
    for intento in range(1, 4):  # 3 intentos
        descargado = 0

        r = requests.get(url, stream=True)
        size_total = int(r.headers.get("content-length", 0))

        with open(ruta_final, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                    descargado += len(chunk)
                    yield descargado, size_total, "descargando"

        # Verificar CRC si viene en XML
        if crc_esperado:
            crc_local = calcular_crc(ruta_final)

            if crc_local == crc_esperado:
                yield descargado, size_total, "ok"
                return  # finaliza archivo correcto
            else:
                # Si CRC falla → retry
                continue
        else:
            # si no tiene CRC, lo marcamos como correcto
            yield descargado, size_total, "ok"
            return

    yield 0, 0, "error"  # tras 3 fallos

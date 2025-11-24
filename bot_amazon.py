import os
import json
import requests
from bs4 import BeautifulSoup
from time import sleep

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "es-ES,es;q=0.9"
}

BATCH_SIZE = 10  # Lotes de 10 productos

# ---------------------------
# Funciones
# ---------------------------
def scrape_amazon(url, retries=3):
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            soup = BeautifulSoup(r.text, "html.parser")

            titulo = soup.select_one("#productTitle")
            titulo = titulo.text.strip() if titulo else "No disponible"

            precio = soup.select_one("#priceblock_ourprice, #priceblock_dealprice, .a-price .a-offscreen")
            precio_actual = precio.text.strip() if precio else "No disponible"

            precio_ant = soup.select_one(".priceBlockStrikePriceString, .a-text-price .a-offscreen")
            precio_anterior = precio_ant.text.strip() if precio_ant else "No disponible"

            img = soup.select_one("#landingImage, #imgTagWrapperId img")
            imagen_url = img.get("src") if img else None

            return titulo, precio_actual, precio_anterior, img
        except Exception as e:
            print(f"[WARN] Error scrapeando {url}: {e}, intento {attempt+1}")
            sleep(2)
    return "Error", "Error", "Error", None

def enviar_mensaje(texto):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": texto, "parse_mode": "Markdown"}
    requests.post(url, data=data)

def enviar_imagen(url_imagen, caption=None):
    if not url_imagen:
        return
    api = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    data = {"chat_id": CHAT_ID, "photo": url_imagen}
    if caption:
        data["caption"] = caption
    requests.post(api, data=data)

def cargar_precios():
    if not os.path.exists("precios.json"):
        return {}
    with open("precios.json", "r") as f:
        return json.load(f)

def guardar_precios(precios):
    with open("precios.json", "w") as f:
        json.dump(precios, f, indent=4)

# ---------------------------
# Función para procesar lote
# ---------------------------
def procesar_lote(lote, precios_previos):
    precios_actuales = {}
    cambios = []

    for producto in lote:
        pid = producto["id"]
        url = producto["url"]

        titulo, precio_actual, precio_ant, imagen = scrape_amazon(url)
        precios_actuales[pid] = precio_actual

        precio_prev = precios_previos.get(pid)

        mensaje = f"""
📦 *Producto:* {titulo}

🖼️ *Imagen*:  
{imagen}

💰 *Precio actual:* {precio_actual}
✖️ *Precio anterior:* ~~{precio_ant}~~

🔗 {url}
"""
        if precio_prev is None or precio_prev != precio_actual:
            if precio_prev is not None:
                enviar_mensaje("⚠️ *CAMBIO DE PRECIO DETECTADO* ⚠️")
            enviar_mensaje(mensaje)
            enviar_imagen(imagen)
            cambios.append(titulo)
            print(f"[INFO] Enviado: {titulo}")
        else:
            print(f"[INFO] Sin cambio: {titulo}")

        sleep(1)  # evita bloqueo por Amazon

    return precios_actuales, cambios

# ---------------------------
# Main
# ---------------------------
if __name__ == "__main__":
    with open("productos.json", "r") as f:
        productos = json.load(f)

    precios_previos = cargar_precios()
    todos_precios = {}
    todos_cambios = []

    # Dividir en lotes
    for i in range(0, len(productos), BATCH_SIZE):
        lote = productos[i:i+BATCH_SIZE]
        precios_lote, cambios_lote = procesar_lote(lote, precios_previos)
        todos_precios.update(precios_lote)
        todos_cambios.extend(cambios_lote)
        print(f"[INFO] Lote {i//BATCH_SIZE + 1} procesado")

    # Guardar precios finales
    guardar_precios(todos_precios)

    # Resumen final
    if todos_cambios:
        resumen = f"✅ Cambios detectados en {len(todos_cambios)} productos:\n"
        for t in todos_cambios:
            resumen += f"• {t}\n"
        enviar_mensaje(resumen)
        print("[INFO] Resumen final enviado")
    else:
        print("[INFO] No se detectaron cambios de precio")

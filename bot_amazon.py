import os
import json
import requests

# Configura secretos de Telegram desde GitHub Actions
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

def send_to_telegram(message, image_url=None):
    """Envía un mensaje a Telegram con logs"""
    try:
        if image_url:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
            r = requests.post(url, data={"chat_id": CHAT_ID, "photo": image_url, "caption": message, "parse_mode": "Markdown"})
        else:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            r = requests.post(url, data={"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"})
        r.raise_for_status()
        print(f"[OK] Mensaje enviado: {message[:50]}...")
        with open("enviados.log", "a", encoding="utf-8") as f:
            f.write(f"{message[:50]}...\n")
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] No se pudo enviar: {e}")

def parse_products(file_path):
    products = []
    with open(file_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
    i = 0
    while i < len(lines):
        asin = lines[i]
        title = lines[i+1]
        image = lines[i+2]
        price_line = lines[i+3]
        prev_price_line = lines[i+4]
        discount_line = lines[i+5]
        url = lines[i+6]

        price = price_line.replace("Precio:", "").replace("Euros", "").strip()
        prev_price = prev_price_line.replace("Precio anterior:", "").replace("Euros", "").strip()
        discount = discount_line.replace("Descuento:", "").strip()

        products.append({
            "asin": asin,
            "title": title,
            "image": image,
            "price": price,
            "prev_price": prev_price,
            "discount": discount,
            "url": url
        })
        i += 7
    return products

def main():
    repo_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(repo_path, "amazon.txt")
    products = parse_products(file_path)

    last_index_file = os.path.join(repo_path, "last_index.json")
    try:
        with open(last_index_file, "r") as f:
            data = json.load(f)
            last_index = data.get("last_index", 0)
    except FileNotFoundError:
        last_index = 0

    product = products[last_index]
    message = f"📦 *Producto:* {product['title']}\n" \
              f"💰 *Precio actual:* {product['price']} €\n" \
              f"💸 *Precio anterior:* {product['prev_price']} €\n" \
              f"🔖 *Descuento:* {product['discount']}\n" \
              f"🔗 {product['url']}"

    send_to_telegram(message, image_url=product['image'])

    next_index = (last_index + 1) % len(products)
    with open(last_index_file, "w") as f:
        json.dump({"last_index": next_index}, f)

if __name__ == "__main__":
    main()

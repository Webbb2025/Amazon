import json
import requests

TELEGRAM_TOKEN = "TU_TELEGRAM_TOKEN"
CHAT_ID = "TU_CHAT_ID"

def send_to_telegram(message, image_url=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    if image_url:
        photo_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
        requests.post(photo_url, data={"chat_id": CHAT_ID, "photo": image_url, "caption": message, "parse_mode": "Markdown"})
    else:
        requests.post(url, data={"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"})

def parse_products(file_path):
    """Lee amazon.txt y devuelve lista de productos"""
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
    products = parse_products("amazon.txt")

    # Guardamos el índice del último producto enviado
    try:
        with open("last_index.json", "r") as f:
            data = json.load(f)
            last_index = data.get("last_index", 0)
    except FileNotFoundError:
        last_index = 0

    # Enviar el producto actual
    product = products[last_index]
    message = f"📦 *Producto:* {product['title']}\n" \
              f"💰 *Precio actual:* {product['price']} €\n" \
              f"💸 *Precio anterior:* {product['prev_price']} €\n" \
              f"🔖 *Descuento:* {product['discount']}\n" \
              f"🔗 {product['url']}"
    
    send_to_telegram(message, image_url=product['image'])
    print(f"Enviado: {product['title']}")

    # Actualizar índice
    next_index = (last_index + 1) % len(products)
    with open("last_index.json", "w") as f:
        json.dump({"last_index": next_index}, f)

if __name__ == "__main__":
    main()

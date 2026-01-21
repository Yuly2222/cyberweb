"""
Bot de notificaciones de checkout vía WhatsApp.

Requisitos previos (Windows):
  pip install flask pywhatkit

Ejecución:
  python whatsbot.py

El checkout llama a http://localhost:5001/notify con un JSON
{name, email, phone, total, items}. Este bot arma un mensaje
y lo envía con pywhatkit al número configurado en TARGET_PHONE.
"""

from flask import Flask, request, jsonify
import pywhatkit
import threading
import datetime
import os

app = Flask(__name__)

# Número de destino en formato internacional, ej: "+573001234567"
TARGET_PHONE = os.environ.get("WHATS_TARGET", "+573108182572")

# Mutex simple para evitar solapamientos de envíos simultáneos
send_lock = threading.Lock()


@app.after_request
def add_cors_headers(response):
	response.headers["Access-Control-Allow-Origin"] = "*"
	response.headers["Access-Control-Allow-Headers"] = "Content-Type"
	response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
	return response


def build_message(payload: dict) -> str:
	name = payload.get("name", "Cliente")
	email = payload.get("email", "")
	phone = payload.get("phone", "")
	total = payload.get("total", 0)
	items = payload.get("items", []) or []

	lines = [
		"Nuevo pedido en Cyberduck",
		f"Nombre: {name}",
		f"Correo: {email}",
		f"Celular: {phone}",
		f"Total: ${total:,.0f}",
		"Productos:",
	]

	for it in items:
		item_name = it.get("name", "Producto")
		price = it.get("price", "")
		lines.append(f"- {item_name} — {price}")

	return "\n".join(lines)


@app.post("/notify")
def notify():
	data = request.get_json(force=True, silent=True) or {}
	print(f"\n{'='*60}")
	print(f"[NOTIFICACIÓN] Pedido recibido:")
	print(f"  Cliente: {data.get('name', 'N/A')}")
	print(f"  Total: ${data.get('total', 0):,.0f}")
	print(f"  Número destino: {TARGET_PHONE}")
	print(f"{'='*60}\n")
	
	message = build_message(data)
	print(f"Mensaje a enviar:\n{message}\n")

	# pywhatkit necesita hora/minuto; usamos envío instantáneo
	with send_lock:
		try:
			print(f"[INFO] Enviando mensaje a WhatsApp...")
			print(f"[INFO] IMPORTANTE: Asegúrate de tener WhatsApp Web abierto en tu navegador")
			pywhatkit.sendwhatmsg_instantly(
				phone_no=TARGET_PHONE,
				message=message,
				wait_time=15,  # segundos para preparar el navegador
				tab_close=True,
				close_time=3,
			)
			print(f"[OK] Mensaje enviado exitosamente!")
		except Exception as exc:  # noqa: BLE001
			print(f"[ERROR] Fallo al enviar: {str(exc)}")
			return jsonify({"status": "error", "detail": str(exc)}), 500

	return jsonify({"status": "ok"})


if __name__ == "__main__":
	# Ejecutar en localhost:5001
	print("\n" + "="*60)
	print("🤖 BOT DE WHATSAPP - CYBERDUCK")
	print("="*60)
	print(f"✓ Servidor iniciado en http://127.0.0.1:5001")
	print(f"✓ Número destino: {TARGET_PHONE}")
	print(f"\n⚠️  IMPORTANTE:")
	print(f"   1. Mantén WhatsApp Web ABIERTO en tu navegador")
	print(f"   2. Escanea el código QR si es necesario")
	print(f"   3. El bot abrirá una nueva pestaña para enviar mensajes")
	print("="*60 + "\n")
	app.run(host="127.0.0.1", port=5001, debug=True)

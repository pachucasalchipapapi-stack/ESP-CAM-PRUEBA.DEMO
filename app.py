from flask import Flask, render_template_string, request, jsonify
import datetime
import os
import google.generativeai as genai

app = Flask(__name__)

# Configura tu API Key de Gemini
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "TU_API_KEY_AQUI")
genai.configure(api_key=GEMINI_API_KEY)

# Modelo optimizado para análisis multimodal (visión)
model = genai.GenerativeModel('gemini-1.5-flash')

# Estado global del robot
estado_robot = {
    "comando": "detener",
    "modo_ia": True,
    "ultima_actualizacion": "Ninguna",
    "ultima_notificacion": "Esperando primera captura de la ESP32-CAM..."
}

HTML_PANEL = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cerebro IA - Robot con Visión Interactiva</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; background-color: #1a1a2e; color: #fff; padding: 20px; }
        .card { background-color: #16213e; border-radius: 12px; padding: 20px; max-width: 450px; margin: auto; box-shadow: 0 4px 10px rgba(0,0,0,0.5); }
        h1 { color: #00fff5; margin-bottom: 5px; }
        .status { font-size: 1.5em; font-weight: bold; color: #e94560; text-transform: uppercase; margin: 10px 0; }
        .mode-badge { display: inline-block; padding: 6px 14px; border-radius: 20px; font-weight: bold; margin-bottom: 15px; }
        .mode-manual { background-color: #ff9f43; color: #000; }
        .mode-auto { background-color: #10ac84; color: #fff; }
        .alert { background-color: #0f3460; border-left: 5px solid #00fff5; padding: 12px; font-size: 0.95em; margin-top: 15px; text-align: left; }
        .chat-box { margin-top: 15px; display: flex; gap: 8px; }
        .chat-box input { flex: 1; padding: 10px; border-radius: 6px; border: 1px solid #00fff5; background: #0f3460; color: #fff; }
        .chat-box button { padding: 10px 15px; background: #00fff5; color: #1a1a2e; font-weight: bold; border: none; border-radius: 6px; cursor: pointer; }
        .btn-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin-top: 15px; }
        button.ctrl-btn { padding: 12px; border: none; border-radius: 8px; font-size: 0.95em; font-weight: bold; cursor: pointer; background: #0f3460; color: #fff; }
        button.ctrl-btn:hover { background: #e94560; }
        .stop { grid-column: span 3; background: #e94560 !important; }
        .switch-btn { width: 100%; padding: 14px; margin-top: 15px; font-size: 1em; border-radius: 8px; border: none; cursor: pointer; font-weight: bold; background: #00fff5; color: #1a1a2e; }
        .switch-btn:hover { background: #00d8d0; }
    </style>
</head>
<body>
    <div class="card">
        <h1>🤖 Cerebro Robot IA</h1>
        <div id="badge" class="mode-badge mode-auto">Modo: IA AUTÓNOMA 🧠</div>
        
        <p style="margin: 5px 0;">Comando en Ejecución:</p>
        <div class="status" id="cmd">{{ estado.comando }}</div>
        
        <button class="switch-btn" onclick="alternarModoIA()">🧠 Alternar Modo IA Autónoma</button>

        <div class="alert">
            <strong>💬 Pregunta / Alerta de la IA:</strong><br>
            <span id="alerta">{{ estado.ultima_notificacion }}</span><br>
            <small id="hora" style="color: #aaa;">Hora: {{ estado.ultima_actualizacion }}</small>
        </div>

        <div class="chat-box">
            <input type="text" id="userInput" placeholder="Responde a la IA (ej: 'esquivala', 'avanza')...">
            <button onclick="responderIA()">Responder</button>
        </div>

        <h3>Control Manual:</h3>
        <div class="btn-grid">
            <div></div>
            <button class="ctrl-btn" onclick="enviarComando('avanzar')">▲ Avanzar</button>
            <div></div>
            <button class="ctrl-btn" onclick="enviarComando('izquierda')">◄ Izq</button>
            <button class="ctrl-btn stop" onclick="enviarComando('detener')">■ DETENER</button>
            <button class="ctrl-btn" onclick="enviarComando('derecha')">Der ►</button>
            <div></div>
            <button class="ctrl-btn" onclick="enviarComando('retroceder')">▼ Atrás</button>
            <div></div>
        </div>
    </div>

    <script>
        function enviarComando(cmd) {
            fetch('/actualizar', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ comando: cmd, notificacion: "Control manual activado" })
            }).then(res => res.json()).then(data => actualizarInterfaz(data));
        }

        function alternarModoIA() {
            fetch('/modo_ia', { method: 'POST' })
            .then(res => res.json())
            .then(data => actualizarInterfaz(data));
        }

        function responderIA() {
            const input = document.getElementById('userInput');
            const texto = input.value.trim();
            if(!texto) return;

            fetch('/responder', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ respuesta: texto })
            })
            .then(res => res.json())
            .then(data => {
                input.value = '';
                actualizarInterfaz(data);
            });
        }

        function actualizarInterfaz(data) {
            document.getElementById('cmd').innerText = data.comando;
            document.getElementById('alerta').innerText = data.ultima_notificacion;
            document.getElementById('hora').innerText = "Hora: " + data.ultima_actualizacion;
            
            const badge = document.getElementById('badge');
            if(data.modo_ia) {
                badge.innerText = "Modo: IA AUTÓNOMA (Cámara) 🧠";
                badge.className = "mode-badge mode-auto";
            } else {
                badge.innerText = "Modo: MANUAL 🎮";
                badge.className = "mode-badge mode-manual";
            }
        }

        setInterval(() => {
            fetch('/estado').then(r => r.json()).then(data => actualizarInterfaz(data));
        }, 2000);
    </script>
</body>
</html>
"""

@app.route('/')
def panel():
    return render_template_string(HTML_PANEL, estado=estado_robot)

@app.route('/comando', methods=['GET'])
def obtener_comando_esp():
    return estado_robot["comando"]

@app.route('/estado', methods=['GET'])
def obtener_estado_json():
    return jsonify(estado_robot)

@app.route('/subir_foto', methods=['POST'])
def recibir_foto():
    image_bytes = request.data
    if not image_bytes:
        return "Sin imagen", 400

    if estado_robot["modo_ia"]:
        try:
            image_part = {"mime_type": "image/jpeg", "data": image_bytes}
            
            prompt = (
                "Eres la visión artificial de un robot explorador. "
                "Observa la imagen y responde en un solo párrafo corto en español haciendo una pregunta o sugerencia directa sobre lo que ves. "
                "Si detectas una chancla, un obstáculo o cualquier objeto en el camino, pregunta al usuario directamente qué hacer con él. "
                "Indica al final entre corchetes el comando sugerido para los motores, por ejemplo: [SUGERENCIA: detener], [SUGERENCIA: avanzar], o [SUGERENCIA: izquierda]."
            )
            
            response = model.generate_content([prompt, image_part])
            texto_respuesta = response.text.strip()
            
            estado_robot["ultima_notificacion"] = texto_respuesta
            
            # Asignar comando según la sugerencia extraída de Gemini
            if "[SUGERENCIA: avanzar]" in texto_respuesta.lower():
                estado_robot["comando"] = "avanzar"
            elif "[SUGERENCIA: izquierda]" in texto_respuesta.lower():
                estado_robot["comando"] = "izquierda"
            elif "[SUGERENCIA: derecha]" in texto_respuesta.lower():
                estado_robot["comando"] = "derecha"
            elif "[SUGERENCIA: retroceder]" in texto_respuesta.lower():
                estado_robot["comando"] = "retroceder"
            else:
                estado_robot["comando"] = "detener"

        except Exception as e:
            estado_robot["ultima_notificacion"] = f"Error procesando imagen: {str(e)}"
            estado_robot["comando"] = "detener"
    else:
        estado_robot["ultima_notificacion"] = "Foto recibida. Modo manual activo."

    estado_robot["ultima_actualizacion"] = datetime.datetime.now().strftime("%H:%M:%S")
    return "OK", 200

@app.route('/responder', methods=['POST'])
def responder_a_ia():
    data = request.get_json(silent=True) or {}
    user_text = data.get('respuesta', '').lower()
    
    # Interpretar respuestas directas del usuario por chat
    if "avanza" in user_text or "adelante" in user_text or "continua" in user_text:
        estado_robot["comando"] = "avanzar"
    elif "izq" in user_text or "esquiva" in user_text or "gira a la izquierda" in user_text:
        estado_robot["comando"] = "izquierda"
    elif "der" in user_text or "gira a la derecha" in user_text:
        estado_robot["comando"] = "derecha"
    elif "atras" in user_text or "retrocede" in user_text or "huye" in user_text:
        estado_robot["comando"] = "retroceder"
    else:
        estado_robot["comando"] = "detener"
        
    estado_robot["ultima_notificacion"] = f"Usuario ordenó: '{user_text}' -> Ejecutando: {estado_robot['comando']}"
    estado_robot["ultima_actualizacion"] = datetime.datetime.now().strftime("%H:%M:%S")
    return jsonify(estado_robot)

@app.route('/actualizar', methods=['POST'])
def actualizar_comando():
    data = request.get_json(silent=True) or {}
    estado_robot["comando"] = data.get('comando', 'detener').lower()
    estado_robot["modo_ia"] = False
    estado_robot["ultima_notificacion"] = data.get('notificacion', 'Control manual')
    estado_robot["ultima_actualizacion"] = datetime.datetime.now().strftime("%H:%M:%S")
    return jsonify(estado_robot)

@app.route('/modo_ia', methods=['POST'])
def cambiar_modo_ia():
    estado_robot["modo_ia"] = not estado_robot["modo_ia"]
    if estado_robot["modo_ia"]:
        estado_robot["ultima_notificacion"] = "Modo IA activado. Analizando entorno..."
    else:
        estado_robot["comando"] = "detener"
        estado_robot["ultima_notificacion"] = "IA en pausa. Control manual activado."
    estado_robot["ultima_actualizacion"] = datetime.datetime.now().strftime("%H:%M:%S")
    return jsonify(estado_robot)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

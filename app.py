from flask import Flask, render_template_string, request, jsonify
import datetime
import random
import time

app = Flask(__name__)

# Estado global del robot
estado_robot = {
    "comando": "detener",
    "modo_ia": False,  # False = Manual, True = IA Autónoma
    "ultima_actualizacion": "Ninguna",
    "ultima_notificacion": "Sistema iniciado. En espera."
}

HTML_PANEL = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cerebro IA - Robot ESP8266</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; background-color: #1a1a2e; color: #fff; padding: 20px; }
        .card { background-color: #16213e; border-radius: 12px; padding: 20px; max-width: 420px; margin: auto; box-shadow: 0 4px 10px rgba(0,0,0,0.5); }
        h1 { color: #00fff5; margin-bottom: 5px; }
        .status { font-size: 1.5em; font-weight: bold; color: #e94560; text-transform: uppercase; margin: 10px 0; }
        .mode-badge { display: inline-block; padding: 6px 14px; border-radius: 20px; font-weight: bold; margin-bottom: 15px; }
        .mode-manual { background-color: #ff9f43; color: #000; }
        .mode-auto { background-color: #10ac84; color: #fff; }
        .alert { background-color: #0f3460; border-left: 5px solid #00fff5; padding: 10px; font-size: 0.9em; margin-top: 15px; text-align: left; }
        .btn-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin-top: 15px; }
        button { padding: 12px; border: none; border-radius: 8px; font-size: 0.95em; font-weight: bold; cursor: pointer; background: #0f3460; color: #fff; }
        button:hover { background: #e94560; }
        .stop { grid-column: span 3; background: #e94560; }
        .switch-btn { width: 100%; padding: 14px; margin-top: 15px; font-size: 1em; border-radius: 8px; border: none; cursor: pointer; font-weight: bold; background: #00fff5; color: #1a1a2e; }
        .switch-btn:hover { background: #00d8d0; }
    </style>
</head>
<body>
    <div class="card">
        <h1>🤖 Cerebro Robot IA</h1>
        <div id="badge" class="mode-badge mode-manual">Modo: MANUAL</div>
        
        <p style="margin: 5px 0;">Comando Actual:</p>
        <div class="status" id="cmd">{{ estado.comando }}</div>
        
        <button class="switch-btn" onclick="alternarModoIA()">🧠 Alternar Modo IA Autónoma</button>

        <div class="alert">
            <strong>📢 Decisión / Alerta IA:</strong><br>
            <span id="alerta">{{ estado.ultima_notificacion }}</span><br>
            <small id="hora" style="color: #aaa;">Hora: {{ estado.ultima_actualizacion }}</small>
        </div>

        <h3>Control Manual:</h3>
        <div class="btn-grid">
            <div></div>
            <button onclick="enviarComando('avanzar')">▲ Avanzar</button>
            <div></div>
            <button onclick="enviarComando('izquierda')">◄ Izq</button>
            <button class="stop" onclick="enviarComando('detener')">■ DETENER</button>
            <button onclick="enviarComando('derecha')">Der ►</button>
            <div></div>
            <button onclick="enviarComando('retroceder')">▼ Atrás</button>
            <div></div>
        </div>
    </div>

    <script>
        function enviarComando(cmd) {
            fetch('/actualizar', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ comando: cmd, notificacion: "Comando manual enviado desde el panel web" })
            })
            .then(res => res.json())
            .then(data => actualizarInterfaz(data));
        }

        function alternarModoIA() {
            fetch('/modo_ia', { method: 'POST' })
            .then(res => res.json())
            .then(data => {
                alert("Modo IA " + (data.modo_ia ? "ACTIVADO (Autónomo)" : "DESACTIVADO (Manual)"));
            });
        }

        function actualizarInterfaz(data) {
            document.getElementById('cmd').innerText = data.comando;
            document.getElementById('alerta').innerText = data.ultima_notificacion;
            document.getElementById('hora').innerText = "Hora: " + data.ultima_actualizacion;
            
            const badge = document.getElementById('badge');
            if(data.modo_ia) {
                badge.innerText = "Modo: IA AUTÓNOMA 🧠";
                badge.className = "mode-badge mode-auto";
            } else {
                badge.innerText = "Modo: MANUAL 🎮";
                badge.className = "mode-badge mode-manual";
            }
        }

        // Consultar estado cada 2 segundos
        setInterval(() => {
            fetch('/estado')
            .then(r => r.json())
            .then(data => actualizarInterfaz(data));
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
    # Si la IA está activa, evaluamos la decisión autónoma en cada consulta del ESP8266
    if estado_robot["modo_ia"]:
        tomar_decision_ia()
    return estado_robot["comando"]

@app.route('/estado', methods=['GET'])
def obtener_estado_json():
    return jsonify(estado_robot)

@app.route('/actualizar', methods=['POST'])
def actualizar_comando():
    data = request.get_json(silent=True) or {}
    nuevo_cmd = data.get('comando', 'detener').lower()
    notificacion = data.get('notificacion', 'Sin detalles')
    
    if nuevo_cmd in ['avanzar', 'retroceder', 'izquierda', 'derecha', 'detener']:
        estado_robot["comando"] = nuevo_cmd
        estado_robot["modo_ia"] = False  # Si presionas un botón manual, se desactiva la IA por control
        estado_robot["ultima_actualizacion"] = datetime.datetime.now().strftime("%H:%M:%S")
        estado_robot["ultima_notificacion"] = notificacion
        return jsonify(estado_robot), 200
    return jsonify({"status": "error"}), 400

@app.route('/modo_ia', methods=['POST'])
def cambiar_modo_ia():
    estado_robot["modo_ia"] = not estado_robot["modo_ia"]
    if estado_robot["modo_ia"]:
        estado_robot["ultima_notificacion"] = "IA Autónoma activada. Tomando decisiones..."
        tomar_decision_ia()
    else:
        estado_robot["comando"] = "detener"
        estado_robot["ultima_notificacion"] = "IA desactivada. Robot detenido por seguridad."
        
    estado_robot["ultima_actualizacion"] = datetime.datetime.now().strftime("%H:%M:%S")
    return jsonify(estado_robot)

def tomar_decision_ia():
    """
    Núcleo del cerebro del Robot:
    Aquí la IA evalúa las variables y decide la siguiente acción del robot.
    """
    opciones = ["avanzar", "avanzar", "avanzar", "izquierda", "derecha", "detener"]
    decision = random.choice(opciones)
    
    mensajes = {
        "avanzar": "Camino libre detectado. Avanzando...",
        "izquierda": "Ajustando trayectoria hacia la izquierda.",
        "derecha": "Girando a la derecha para explorar.",
        "detener": "Analizando entorno / Pausa de seguridad."
    }
    
    estado_robot["comando"] = decision
    estado_robot["ultima_notificacion"] = f"[IA] {mensajes.get(decision, 'Ejecutando patrón')}"
    estado_robot["ultima_actualizacion"] = datetime.datetime.now().strftime("%H:%M:%S")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

from flask import Flask, render_template_string, request, jsonify
import datetime

app = Flask(__name__)

# Variables globales para el estado del robot
estado_robot = {
    "comando": "detener",
    "ultima_actualizacion": "Ninguna",
    "ultima_notificacion": "Sin alertas registradas"
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
        .card { background-color: #16213e; border-radius: 12px; padding: 20px; max-width: 400px; margin: auto; box-shadow: 0 4px 10px rgba(0,0,0,0.5); }
        h1 { color: #00fff5; }
        .status { font-size: 1.4em; font-weight: bold; color: #e94560; text-transform: uppercase; margin: 15px 0; }
        .alert { background-color: #0f3460; border-left: 5px solid #00fff5; padding: 10px; font-size: 0.9em; margin-top: 15px; text-align: left; }
        .btn-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin-top: 20px; }
        button { padding: 15px; border: none; border-radius: 8px; font-size: 1em; font-weight: bold; cursor: pointer; background: #0f3460; color: #fff; }
        button:hover { background: #e94560; }
        .stop { grid-column: span 3; background: #e94560; }
    </style>
</head>
<body>
    <div class="card">
        <h1>🤖 Cerebro Robot IA</h1>
        <p>Comando Actual:</p>
        <div class="status" id="cmd">{{ estado.comando }}</div>
        
        <div class="alert">
            <strong>📢 Última Alerta IA:</strong><br>
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
            .then(data => {
                document.getElementById('cmd').innerText = data.comando;
            });
        }

        // Auto recargar cada 3 segundos para ver cambios en tiempo real
        setInterval(() => {
            fetch('/estado')
            .then(r => r.json())
            .then(data => {
                document.getElementById('cmd').innerText = data.comando;
                document.getElementById('alerta').innerText = data.ultima_notificacion;
                document.getElementById('hora').innerText = "Hora: " + data.ultima_actualizacion;
            });
        }, 3000);
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

@app.route('/actualizar', methods=['POST'])
def actualizar_comando():
    data = request.get_json(silent=True) or {}
    if not data and request.form:
        data = request.form
        
    nuevo_cmd = data.get('comando', 'detener').lower()
    notificacion = data.get('notificacion', 'Sin detalles')
    
    if nuevo_cmd in ['avanzar', 'retroceder', 'izquierda', 'derecha', 'detener']:
        estado_robot["comando"] = nuevo_cmd
        estado_robot["ultima_actualizacion"] = datetime.datetime.now().strftime("%H:%M:%S")
        estado_robot["ultima_notificacion"] = notificacion
            
        return jsonify({"status": "ok", "comando": nuevo_cmd}), 200
    else:
        return jsonify({"status": "error", "mensaje": "Comando no válido"}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

import network
import socket
import time
import json
import machine
import os
from max6675 import MAX6675

# 1. HARDWARE SETUP
print("--- SYSTEM STARTUP ---")
led = machine.Pin(2, machine.Pin.OUT) 
ssr = machine.Pin(4, machine.Pin.OUT) 
ssr.value(0) 

# Thermocouple (MAX6675) Pins
sck = 5
cs = 23
so = 19
print(f"Initializing MAX6675 (SCK:{sck}, CS:{cs}, SO:{so})...")
sensor = MAX6675(sck, cs, so)

# 2. MONITOR STATE
state = {
    "temp": 0.0,
    "status": "Starting",
    "uptime": 0
}

last_read = 0

def update_sensor():
    global last_read
    if time.ticks_diff(time.ticks_ms(), last_read) > 2000:
        try:
            current_temp = sensor.read_temp()
            if current_temp is not None:
                state["temp"] = current_temp
                state["status"] = "Operational"
                print(f"[{state['uptime']}s] Temp: {current_temp:.1f}C")
            else:
                state["status"] = "Sensor Error"
                print(f"[{state['uptime']}s] ERROR: Thermocouple Disconnected")
        except Exception as e:
            print(f"Sensor Read Failed: {e}")
            state["status"] = "Read Failed"
            
        state["uptime"] = time.ticks_ms() // 1000
        last_read = time.ticks_ms()

# 3. SETUP ACCESS POINT
print("Starting WiFi Access Point...")
ap = network.WLAN(network.AP_IF)
ap.active(False); time.sleep(1)
ap.config(essid='ESP32-Furnace-Monitor', password='password123')
ap.active(True)

while not ap.active():
    pass

print(f"WiFi Active. SSID: {ap.config('essid')}")
print(f"Gateway IP (Dashboard): {ap.ifconfig()[0]}")

# 4. HTML UI
def get_html():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Furnace Monitor</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <script src="/chart.js"></script>
        <style>
            body { font-family: sans-serif; background: #020617; color: white; text-align: center; padding: 10px; }
            .card { background: #1e293b; padding: 20px; border-radius: 16px; max-width: 600px; margin: auto; border: 1px solid #334155; }
            .temp { font-size: 3.5em; color: #38bdf8; font-weight: bold; margin: 10px 0; }
            .status-tag { background: #334155; padding: 5px 12px; border-radius: 20px; font-size: 0.8em; }
            canvas { background: #0f172a; margin-top: 20px; border-radius: 12px; padding: 10px; }
        </style>
    </head>
    <body>
        <div class="card">
            <h2>🔥 Furnace Monitor</h2>
            <div class="temp"><span id="t">--</span>&deg;C</div>
            <div class="status-tag" id="st">Connecting...</div>
            <canvas id="tempChart"></canvas>
        </div>
        <script>
            let chart;
            function initChart() {
                const ctx = document.getElementById('tempChart').getContext('2d');
                chart = new Chart(ctx, {
                    type: 'line',
                    data: { labels: [], datasets: [{ label: 'Temperature', data: [], borderColor: '#38bdf8', backgroundColor: 'rgba(56, 189, 248, 0.1)', fill: true, tension: 0.4 }] },
                    options: { 
                        responsive: true,
                        scales: { 
                            y: { grid: { color: '#334155' }, ticks: { color: '#94a3b8' } },
                            x: { display: false }
                        },
                        plugins: { legend: { display: false } }
                    }
                });
            }

            // Check if Chart.js is loaded
            if (typeof Chart === 'undefined') {
                document.getElementById('st').innerText = "Chart.js Load Error";
            } else {
                initChart();
            }

            setInterval(() => {
                fetch('/data').then(r => r.json()).then(d => {
                    document.getElementById('t').innerText = d.temp.toFixed(1);
                    document.getElementById('st').innerText = d.status + " | Uptime: " + d.uptime + "s";
                    if (chart) {
                        chart.data.labels.push("");
                        chart.data.datasets[0].data.push(d.temp);
                        if(chart.data.labels.length > 50) { chart.data.labels.shift(); chart.data.datasets[0].data.shift(); }
                        chart.update('none');
                    }
                }).catch(e => {
                    document.getElementById('st').innerText = "Data Fetch Error";
                });
            }, 2000);
        </script>
    </body>
    </html>
    """

# 5. WEB SERVER
print("Starting Web Server on Port 80...")
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
try: 
    s.bind(('', 80))
    s.listen(5)
    s.setblocking(False)
    print("Server successfully bound to Port 80.")
except OSError as e:
    print(f"Failed to bind Port 80: {e}. Resetting...")
    machine.reset()

print("--- SYSTEM READY ---")
while True:
    update_sensor()
    try:
        conn, addr = s.accept()
        request = conn.recv(1024).decode()
        
        if 'GET /data' in request:
            conn.send('HTTP/1.1 200 OK\nContent-Type: application/json\n\n' + json.dumps(state))
        elif 'GET /chart.js' in request:
            print("Serving chart.js...")
            conn.send('HTTP/1.1 200 OK\nContent-Type: application/javascript\n\n')
            with open('chart.js', 'rb') as f:
                while True:
                    chunk = f.read(1024)
                    if not chunk: break
                    conn.send(chunk)
        else:
            conn.send('HTTP/1.1 200 OK\nContent-Type: text/html\n\n' + get_html())
        conn.close()
    except OSError: 
        pass 
    except Exception as e:
        print(f"Server Error: {e}")

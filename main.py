import network
import socket
import time
import json
import machine
from max6675 import MAX6675

# 1. HARDWARE SETUP
print("--- FURNACE SYSTEM STARTUP ---")
ssr = machine.Pin(4, machine.Pin.OUT) 
ssr.value(1) # Relay OFF (Active Low)

# Thermocouple (MAX6675) Pins
sck = 5; cs = 23; so = 19
sensor = MAX6675(sck, cs, so)

# 2. STATE & PID PARAMETERS
state = {
    "temp": 0.0, 
    "setpoint": 150.0, 
    "status": "Operational", 
    "output_pct": 0.0,
    "manual_mode": True,
    "uptime": 0
}

kp = 2.0; ki = 0.1; kd = 0.5
integral = 0.0; last_error = 0.0; last_time = time.ticks_ms()
cycle_start = time.ticks_ms()
cycle_ms = 10000 

def run_control_cycle():
    global integral, last_error, last_time, cycle_start
    now = time.ticks_ms()
    
    # A. PID UPDATE (Every 2 seconds)
    dt = time.ticks_diff(now, last_time) / 1000.0
    if dt >= 2.0:
        last_time = now
        current_temp = sensor.read_temp()
        if current_temp is None:
            state["status"] = "Sensor Error"; ssr.value(1); return
        
        state["temp"] = current_temp
        state["status"] = "Operational"
        state["uptime"] = now // 1000
        
        if not state["manual_mode"]:
            error = state["setpoint"] - current_temp
            p_out = kp * error
            if 0 < state["output_pct"] < 100: integral += error * dt
            i_out = ki * integral
            d_out = kd * (error - last_error) / dt
            last_error = error
            state["output_pct"] = max(0, min(100, p_out + i_out + d_out))
        
        mode_str = "MAN" if state["manual_mode"] else "PID"
        print("UP:{}s | MD:{} | T:{}C | PWR:{}%".format(state['uptime'], mode_str, int(current_temp), int(state['output_pct'])))

    # B. NON-BLOCKING RELAY CONTROL
    # Calculate where we are in the 10-second cycle
    ms_into_cycle = time.ticks_diff(now, cycle_start)
    if ms_into_cycle >= cycle_ms:
        cycle_start = now
        ms_into_cycle = 0
        
    on_ms = int((state["output_pct"] / 100.0) * cycle_ms)
    
    if ms_into_cycle < on_ms:
        ssr.value(0) # Relay ON (Active Low)
    else:
        ssr.value(1) # Relay OFF (Active Low)

# 3. SETUP ACCESS POINT
ap = network.WLAN(network.AP_IF)
ap.active(False); time.sleep(1)
ap.config(essid='ESP32-Furnace-Control', password='password123')
ap.active(True)

# 4. WEB SERVER
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
try: s.bind(('', 80)); s.listen(5); s.setblocking(False)
except OSError: machine.reset()

print("--- SYSTEM READY ---")
while True:
    run_control_cycle()
    try:
        conn, addr = s.accept()
        request = conn.recv(1024).decode()
        
        if 'GET /data' in request:
            conn.send('HTTP/1.1 200 OK\nContent-Type: application/json\n\n' + json.dumps(state))
        elif 'GET /set_target' in request:
            try:
                val = float(request.split('val=')[1].split(' ')[0])
                state["setpoint"] = val
                integral = 0
            except: pass
            conn.send('HTTP/1.1 200 OK\n\nOK')
        elif 'GET /toggle_mode' in request:
            state["manual_mode"] = not state["manual_mode"]
            state["output_pct"] = 0
            conn.send('HTTP/1.1 200 OK\n\nOK')
        elif 'GET /set_power' in request:
            try:
                val = float(request.split('val=')[1].split(' ')[0])
                state["output_pct"] = max(0, min(100, val))
            except: pass
            conn.send('HTTP/1.1 200 OK\n\nOK')
        elif 'GET /chart.js' in request:
            conn.send('HTTP/1.1 200 OK\nContent-Type: application/javascript\nCache-Control: public, max-age=31536000\n\n')
            with open('chart.js', 'rb') as f:
                while True:
                    chunk = f.read(1024); 
                    if not chunk: break
                    conn.send(chunk)
        else:
            conn.send('HTTP/1.1 200 OK\nContent-Type: text/html\n\n')
            with open('index.html', 'rb') as f:
                while True:
                    chunk = f.read(1024); 
                    if not chunk: break
                    conn.send(chunk)
        conn.close()
    except OSError: pass
    except Exception as e: print(f"Server Error: {e}")

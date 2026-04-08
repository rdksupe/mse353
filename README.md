# MSE353: IoT-Enabled PID Furnace Controller
**Project by Group: FatiguedMaterialScientists**

This project implements a high-precision, web-enabled temperature control system for laboratory furnaces. It utilizes a Proportional-Integral-Derivative (PID) algorithm running on an ESP32 to provide stable thermal management, replacing traditional, inefficient On/Off (Bang-Bang) controllers.

---

## System Features
- **Precise PID Control:** Minimizes temperature overshoot and steady-state error.
- **Web Dashboard:** Real-time data visualization via Chart.js.
- **Offline Capability:** Serves all assets (HTML/JS) directly from ESP32 flash memory—no internet required.
- **Master Safety Switch:** Global "Start/Stop" furnace control with a software-defined kill-switch.
- **Manual Mode:** Slider-based power control for hardware verification and characterization.
- **Responsive UI:** Non-blocking asynchronous firmware ensures an instant response to user inputs.

---

## Hardware Architecture
### 1. Components
- **MCU:** ESP32 (NodeMCU-32S)
- **Sensor:** K-type Thermocouple with MAX6675 SPI Interface.
- **Actuator:** Songle SRD-05VDC Mechanical Relay Module (Active Low).
- **Prototype Load:** Bulb-based thermal box for bench testing.

### 2. Wiring Diagram (Final Pinout)
| Component | Pin Label | ESP32 GPIO | Power Source |
| :--- | :--- | :--- | :--- |
| **Relay (IN1)** | D4 | GPIO 4 | -- |
| **MAX6675 (SCK)** | D5 | GPIO 5 | -- |
| **MAX6675 (CS)** | D23 | GPIO 23 | -- |
| **MAX6675 (SO/DO)**| D19 | GPIO 19 | -- |
| **Relay VCC** | VCC | **VIN (5V)** | USB Power |
| **MAX6675 VCC** | VCC | **3.3V** | ESP Regulator |

---

## Software & Logic
### 1. PID Theory
The system calculates the heater power ($u(t)$) based on:
- **Proportional ($K_p=2.0$):** Reactive response to current error.
- **Integral ($K_i=0.1$):** Correction of long-term drift (includes Anti-Windup logic).
- **Derivative ($K_d=0.5$):** Predictive damping to prevent overshoot.

### 2. Time-Proportioned Control
Because mechanical relays cannot be "dimmed," we use a 10-second duty cycle:
- **40% Power** = Relay ON for 4s, OFF for 6s.
- This balance protects the mechanical life of the relay while maintaining thermal stability.

---

## Installation & Deployment
### 1. Prepare ESP32
Flash the latest MicroPython firmware using esptool.py:
```bash
esptool.py --port /dev/ttyUSB0 erase_flash
esptool.py --port /dev/ttyUSB0 write_flash -z 0x1000 ESP32_GENERIC.bin
```

### 2. Upload Project Files
Copy all files to the ESP32 root using mpremote:
```bash
./.venv/bin/mpremote connect /dev/ttyUSB0 cp max6675.py :
./.venv/bin/mpremote connect /dev/ttyUSB0 cp index.html :
./.venv/bin/mpremote connect /dev/ttyUSB0 cp chart.js :
./.venv/bin/mpremote connect /dev/ttyUSB0 cp main.py :
./.venv/bin/mpremote connect /dev/ttyUSB0 soft-reset
```

---

## Usage
1. Connect to the WiFi Access Point: ESP32-Furnace-Control (Password: password123).
2. Open your browser and navigate to http://192.168.4.1.
3. Click **START FURNACE** to begin the PID cycle.
4. Adjust the **Target Temperature** or switch to **Manual Mode** for direct power control.

---

## Safety Warnings
- **High Voltage:** The relay switches 220V AC. Ensure all AC connections are insulated and fused.
- **Relay Life:** Do not reduce the cycle_ms below 5000ms for mechanical relays.
- **Sensor Error:** The firmware will automatically cut power if the thermocouple is disconnected.

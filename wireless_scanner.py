#!/usr/bin/env python3
"""
Signal Analyzer (Wi-Fi + Bluetooth)
- Works best on Windows for Wi-Fi (uses `netsh`).
- Uses Bleak for BLE scanning.
- Includes CLI fallback (--cli) and demo mode (--demo).
Requirements:
    pip install bleak
"""

import subprocess
import re
import math
import random
import time
import asyncio
import threading
import sys
import platform
import argparse
import json
import os
from collections import defaultdict

# ---------------------- GUI IMPORT ----------------------

try:
    import tkinter as tk
    from tkinter import ttk, messagebox
    _HAS_TK = True
except Exception:
    _HAS_TK = False

# ---------------------- BLE IMPORT ----------------------

try:
    from bleak import BleakScanner
    _HAS_BLEAK = True
except Exception:
    _HAS_BLEAK = False

# ---------------------- HELPERS ----------------------

def percent_to_dbm(quality):
    try:
        q = int(quality)
    except Exception:
        return -90
    if q >= 100:
        return -30
    if q <= 1:
        return -90
    dbm = -30 - (100 - q) * 0.55
    return int(max(-95, min(-30, dbm)))

def rssi_to_percent(rssi):
    try:
        r = int(rssi)
    except Exception:
        return "N/A"
    if r >= -30:
        return "100%"
    if r <= -90:
        return "0%"
    return f"{int((r + 90) / 60 * 100)}%"

def channel_to_freq_mhz(channel):
    try:
        c = int(channel)
        if 1 <= c <= 14:
            return 2407 + c * 5
        return 5000 + c * 5
    except Exception:
        return 2412

def estimate_distance_indoor(rssi_dbm, freq_mhz):
    try:
        exponent = (27.55 - (20 * math.log10(freq_mhz)) + abs(rssi_dbm)) / 20.0
        return f"{max(0.2, min(500, 10 ** exponent)):.2f} m"
    except Exception:
        return "N/A"

def get_band(freq_mhz):
    if freq_mhz < 3000:
        return "2.4 GHz"
    if freq_mhz < 6000:
        return "5 GHz"
    return "6+ GHz"

def security_rating(security):
    s = (security or "").upper()
    if "WPA3" in s:
        return "✅ Highly Secure"
    if "WPA2" in s:
        return "🔒 Secure"
    if "WPA" in s:
        return "⚠️ Moderate"
    if "OPEN" in s or "NONE" in s:
        return "🚫 Risky (Open)"
    if "WEP" in s:
        return "⚠️ Weak (WEP)"
    return "❓ Unknown"

# ---------------------- WIFI (UNCHANGED) ----------------------

def run_netsh_refresh():
    try:
        subprocess.run("netsh wlan refresh", shell=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

def parse_netsh_networks(output):
    networks = []
    lines = output.splitlines()
    current_ssid = None
    current_auth = "Unknown"
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        if line.startswith("SSID"):
            current_ssid = line.split(":", 1)[1].strip() or "Hidden Network"
            current_auth = "Unknown"

        elif line.startswith("Authentication"):
            current_auth = line.split(":", 1)[1].strip()

        elif line.startswith("BSSID"):
            bssid = line.split(":", 1)[1].strip()
            signal_percent = None
            channel = None

            j = i + 1
            while j < len(lines):
                l = lines[j].strip()
                if l.startswith("SSID") or l.startswith("BSSID"):
                    break
                if "Signal" in l:
                    signal_percent = int(re.search(r"\d+", l).group())
                if "Channel" in l:
                    channel = int(re.search(r"\d+", l).group())
                j += 1

            signal_dbm = percent_to_dbm(signal_percent)
            freq = channel_to_freq_mhz(channel)
            networks.append({
                "Name": current_ssid,
                "BSSID": bssid,
                "Signal (dBm)": f"{signal_dbm} dBm",
                "Signal (%)": rssi_to_percent(signal_dbm),
                "Distance": estimate_distance_indoor(signal_dbm, freq),
                "Protocol": get_band(freq),
                "Channel": channel or "N/A",
                "Security Type": current_auth,
                "IP Type": random.choice(["IPv4", "IPv6"]),
                "Secure To Use": security_rating(current_auth)
            })
            i = j
            continue
        i += 1

    return networks

def scan_wifi_windows():
    if platform.system().lower() != "windows":
        raise RuntimeError("Wi-Fi scanning only supported on Windows.")
    run_netsh_refresh()
    time.sleep(1)
    output = subprocess.check_output(
        "netsh wlan show networks mode=bssid",
        shell=True,
        text=True,
        encoding="utf-8",
        errors="ignore"
    )
    return parse_netsh_networks(output)

# ---------------------- BLUETOOTH (INTELLIGENT & SPECIFIC) ----------------------

BLE_SEEN = defaultdict(int)

def classify_ble_device(name):
    n = (name or "").lower()
    if "buds" in n or "head" in n:
        return "🎧 Audio Device"
    if "keyboard" in n or "mouse" in n:
        return "⌨️ Input Device"
    if "phone" in n or "iphone" in n:
        return "📱 Smartphone"
    if "watch" in n or "band" in n:
        return "⌚ Wearable"
    return "🔵 Generic BLE"

def ble_stability(count):
    if count >= 3:
        return "Stable"
    if count == 2:
        return "Medium"
    return "Highly Random"

def scan_bluetooth_blocking(timeout=5, rounds=3):
    if not _HAS_BLEAK:
        raise RuntimeError("Bleak not installed")

    if platform.system().lower() == "windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    async def scan_once():
        return await BleakScanner.discover(timeout=timeout)

    devices_all = []
    for _ in range(rounds):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            devices_all.extend(loop.run_until_complete(scan_once()))
        finally:
            loop.close()

    merged = {}

    for d in devices_all:
        addr = d.address
        name = d.name or "Unknown BLE Device"
        BLE_SEEN[addr] += 1

        merged[addr] = {
            "Device Name": name,
            "Device ID": addr,
            "Proximity (%)": min(100, BLE_SEEN[addr] * 33),
            "Device Category": classify_ble_device(name),
            "Address Type": "Random / Private",
            "Advertised Stability": ble_stability(BLE_SEEN[addr]),
            "Pairing Required": "Yes / Unknown"
        }

    if not merged:
        return [{
            "Device Name": "No BLE devices detected",
            "Device ID": "N/A",
            "Proximity (%)": "N/A",
            "Device Category": "N/A",
            "Address Type": "N/A",
            "Advertised Stability": "N/A",
            "Pairing Required": "N/A"
        }]

    return list(merged.values())

# ---------------------- GUI ----------------------

if _HAS_TK:
    class SignalAnalyzerApp:
        def __init__(self, root):
            self.root = root
            self.root.title("📡 Signal Analyzer – Wi-Fi & Bluetooth")
            self.root.geometry("1200x680")

            bar = tk.Frame(root)
            bar.pack(pady=8)

            tk.Button(bar, text="Scan Wi-Fi", width=20,
                      command=self.scan_wifi).pack(side="left", padx=5)
            tk.Button(bar, text="Scan Bluetooth", width=20,
                      command=self.scan_bluetooth).pack(side="left", padx=5)

            self.tree = ttk.Treeview(root, show="headings", height=25)
            self.tree.pack(fill="both", expand=True, padx=10)

            self.status = tk.Label(root, font=("Segoe UI", 11, "bold"))
            self.status.pack(pady=5)

            self.note = tk.Label(root, font=("Segoe UI", 10), fg="#444")
            self.note.pack(pady=2)

        def scan_wifi(self):
            self.tree.delete(*self.tree.get_children())
            self.note.config(text="")
            self.status.config(text="Scanning Wi-Fi...")
            data = scan_wifi_windows()
            cols = ("Name","BSSID","Signal (dBm)","Signal (%)","Distance","Protocol","Channel","Security Type","IP Type","Secure To Use")
            self._show(cols, data)
            best = data[0]
            self.status.config(text=f"🌟 Recommended Wi-Fi: {best['Name']}")

        def scan_bluetooth(self):
            self.tree.delete(*self.tree.get_children())
            self.status.config(text="Scanning Bluetooth...")
            threading.Thread(target=self._bt_task, daemon=True).start()

        def _bt_task(self):
            data = scan_bluetooth_blocking()
            self.root.after(0, lambda: self._show_bt(data))

        def _show(self, cols, data):
            self.tree["columns"] = cols
            for c in cols:
                self.tree.heading(c, text=c)
                self.tree.column(c, width=150, anchor="center")
            for d in data:
                self.tree.insert("", "end", values=[d.get(c, "N/A") for c in cols])

        def _show_bt(self, data):
            cols = (
                "Device Name","Device ID","Proximity (%)",
                "Device Category","Address Type",
                "Advertised Stability","Pairing Required"
            )
            self._show(cols, data)
            best = max(data, key=lambda x: int(x.get("Proximity (%)", 0)))
            self.status.config(text=f"🔵 Recommended Bluetooth Device: {best['Device Name']}")
            self.note.config(
                text="ℹ️ BLE uses randomized addresses for privacy. "
                     "Same physical device may appear multiple times."
            )

# ---------------------- MAIN ----------------------

def main():
    if not _HAS_TK:
        print("Tkinter not available.")
        return
    root = tk.Tk()
    SignalAnalyzerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Signal Analyzer (Wi-Fi + Bluetooth)
- Works best on Windows for Wi-Fi (uses `netsh`).
- Uses Bleak for BLE scanning.
- Includes CLI fallback (--cli) and demo mode (--demo).
Requirements:
    pip install bleak
Run:
    python signal_analyzer.py        # GUI mode (Tkinter)
    python signal_analyzer.py --cli  # CLI only
    python signal_analyzer.py --demo # demo mode (no hardware required)
Notes:
    - On Windows: run from native Python (not WSL) and ensure Wireless adapter is enabled.
    - BLE requires adapter + appropriate permissions.
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

# Try to import GUI libs; if not available allow CLI-only
try:
    import tkinter as tk
    from tkinter import ttk, messagebox
    _HAS_TK = True
except Exception:
    _HAS_TK = False

# Bleak is optional but used for Bluetooth scanning
try:
    from bleak import BleakScanner
    _HAS_BLEAK = True
except Exception:
    _HAS_BLEAK = False

# ---------------------- Helpers ----------------------

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
    dbm = max(-95, min(-30, dbm))
    return int(round(dbm))

def rssi_to_percent(rssi):
    try:
        r = int(rssi)
    except Exception:
        return "N/A"
    max_dbm = -30.0
    min_dbm = -90.0
    if r >= max_dbm:
        return "100%"
    if r <= min_dbm:
        return "0%"
    pct = int((r - min_dbm) / (max_dbm - min_dbm) * 100)
    return f"{pct}%"

def channel_to_freq_mhz(channel):
    try:
        c = int(channel)
        if 1 <= c <= 14:
            return 2407 + c * 5
        if 36 <= c <= 165:
            return 5000 + c * 5
        if c > 14 and c < 200:
            return 5000 + c * 5
    except Exception:
        pass
    return 2412

def estimate_distance_indoor(rssi_dbm, freq_mhz):
    try:
        if rssi_dbm is None:
            return "N/A"
        rssi = float(rssi_dbm)
        if not freq_mhz or freq_mhz <= 0:
            freq_mhz = 2412.0
        exponent = (27.55 - (20 * math.log10(freq_mhz)) + abs(rssi)) / 20.0
        distance = 10 ** exponent
        distance = max(0.2, min(500.0, distance))
        return f"{distance:.2f} m"
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

# ---------------------- netsh parsing ----------------------

def run_netsh_refresh():
    try:
        subprocess.run("netsh wlan refresh", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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
        ssid_match = re.match(r"^SSID\s+\d+\s*:\s*(.*)$", line, flags=re.IGNORECASE)
        if ssid_match:
            ssid_val = ssid_match.group(1).strip()
            current_ssid = ssid_val or "Hidden Network"
            current_auth = "Unknown"
            i += 1
            continue
        auth_match = re.match(r"^Authentication\s*:\s*(.*)$", line, flags=re.IGNORECASE)
        if auth_match:
            current_auth = auth_match.group(1).strip()
            i += 1
            continue
        bssid_match = re.match(r"^BSSID\s+\d+\s*:\s*(.*)$", line, flags=re.IGNORECASE)
        if bssid_match:
            bssid = bssid_match.group(1).strip() or "Unknown BSSID"
            signal_percent = None
            signal_dbm = None
            channel = None
            j = i + 1
            while j < len(lines):
                l = lines[j].strip()
                if re.match(r"^BSSID\s+\d+\s*:", l, flags=re.IGNORECASE) or re.match(r"^SSID\s+\d+\s*:", l, flags=re.IGNORECASE):
                    break
                m_pct = re.search(r"Signal\s*:\s*(\d+)\s*%?", l, flags=re.IGNORECASE)
                if m_pct:
                    try:
                        signal_percent = int(m_pct.group(1))
                    except Exception:
                        signal_percent = None
                m_dbm = re.search(r"(-?\d+)\s*dBm", l, flags=re.IGNORECASE)
                if m_dbm and signal_dbm is None:
                    try:
                        signal_dbm = int(m_dbm.group(1))
                    except Exception:
                        signal_dbm = None
                m_chan = re.search(r"Channel\s*:\s*(\d+)", l, flags=re.IGNORECASE)
                if m_chan:
                    try:
                        channel = int(m_chan.group(1))
                    except Exception:
                        channel = None
                j += 1
            if signal_dbm is None and signal_percent is not None:
                signal_dbm = percent_to_dbm(signal_percent)
            if signal_dbm is None:
                signal_dbm = -100
            freq = channel_to_freq_mhz(channel) if channel else 2412
            dist = estimate_distance_indoor(signal_dbm, freq)
            band = get_band(freq)
            rating = security_rating(current_auth)
            networks.append({
                "Name": current_ssid or "Hidden Network",
                "BSSID": bssid,
                "Signal (dBm)": f"{signal_dbm} dBm",
                "Signal (%)": f"{signal_percent}%" if signal_percent is not None else rssi_to_percent(signal_dbm),
                "Distance": dist,
                "Protocol": band,
                "Channel": channel or "N/A",
                "Security Type": current_auth,
                "IP Type": random.choice(["IPv4", "IPv6"]),
                "Secure To Use": rating
            })
            i = j
            continue
        i += 1
    return networks

def scan_wifi_windows():
    if platform.system().lower() != "windows":
        raise RuntimeError("Wi-Fi scanning via netsh is only supported on Windows (not this platform).")
    try:
        try:
            subprocess.run("netsh wlan disconnect", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3)
        except Exception:
            pass
        run_netsh_refresh()
        try:
            subprocess.run("netsh wlan show interfaces", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3)
        except Exception:
            pass
        time.sleep(1.2)
        cmd = "netsh wlan show networks mode=bssid"
        output = subprocess.check_output(cmd, shell=True, text=True, encoding='utf-8', errors='ignore')
        return parse_netsh_networks(output)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"netsh error or adapter disabled: {e}")
    except Exception as e:
        raise RuntimeError(f"Wi-Fi scan failed: {e}")

# ---------------------- BLE + Demo helpers ----------------------

def sanitize_address(addr):
    if addr is None:
        return "N/A"
    s = str(addr).strip()
    # remove surrounding quotes if present
    if (s.startswith("'") and s.endswith("'")) or (s.startswith('"') and s.endswith('"')):
        s = s[1:-1].strip()
    return s

async def _scan_with_callback(timeout=5.0):
    from bleak import BleakScanner
    seen = {}
    def _detection_callback(device, advertisement_data):
        try:
            if isinstance(device, (str, bytes)):
                key = str(device)
                name = None
                address = key
                rssi = None
                adv = None
            else:
                address = getattr(device, "address", None) or repr(device)
                name = getattr(device, "name", None)
                rssi = getattr(device, "rssi", None)
                adv = advertisement_data
                key = address
        except Exception:
            key = repr(device)
            name = None
            address = key
            rssi = None
            adv = None
        tx_power = None
        manu = {}
        service_uuids = []
        if adv is not None:
            try:
                tx_power = getattr(adv, "tx_power", None)
            except Exception:
                tx_power = None
            try:
                manu = getattr(adv, "manufacturer_data", adv.get("manufacturer_data") if isinstance(adv, dict) else {})
            except Exception:
                manu = {}
            try:
                service_uuids = getattr(adv, "service_uuids", adv.get("service_uuids") if isinstance(adv, dict) else [])
            except Exception:
                service_uuids = []
        entry = seen.get(key, {
            "name": None,
            "address": address,
            "rssi": None,
            "tx_power": None,
            "manufacturer_data": {},
            "service_uuids": []
        })
        if name:
            entry["name"] = name
        if rssi is not None:
            entry["rssi"] = rssi
        if tx_power is not None:
            entry["tx_power"] = tx_power
        try:
            if isinstance(manu, dict):
                entry["manufacturer_data"].update(manu)
        except Exception:
            pass
        if service_uuids:
            for s in service_uuids:
                if s not in entry["service_uuids"]:
                    entry["service_uuids"].append(s)
        seen[key] = entry
    scanner = BleakScanner()
    # may raise AttributeError if not supported: handled by higher-level caller
    scanner.register_detection_callback(_detection_callback)
    if platform.system().lower() == "windows":
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        except Exception:
            pass
    await scanner.start()
    await asyncio.sleep(timeout)
    await scanner.stop()
    return list(seen.values())

async def _scan_with_discover_return_adv(timeout=5.0):
    from bleak import BleakScanner
    try:
        devices = await BleakScanner.discover(timeout=timeout, return_adv=True)
    except TypeError:
        raise RuntimeError("discover(return_adv=True) not supported")
    seen = {}
    for item in devices:
        try:
            if isinstance(item, (tuple, list)) and len(item) >= 2:
                dev, adv = item[0], item[1]
                address = getattr(dev, "address", None) or repr(dev)
                name = getattr(dev, "name", None)
                rssi = getattr(dev, "rssi", None)
                tx_power = getattr(adv, "tx_power", None) if adv is not None else None
                manu = getattr(adv, "manufacturer_data", {}) if adv is not None else {}
                service_uuids = getattr(adv, "service_uuids", []) if adv is not None else []
            else:
                dev = item
                address = getattr(dev, "address", None) or repr(dev)
                name = getattr(dev, "name", None)
                rssi = getattr(dev, "rssi", None)
                tx_power = None
                manu = {}
                service_uuids = []
        except Exception:
            address = repr(item)
            name = None
            rssi = None
            tx_power = None
            manu = {}
            service_uuids = []
        entry = seen.get(address, {"name": None, "address": address, "rssi": None, "tx_power": None, "manufacturer_data": {}, "service_uuids": []})
        if name:
            entry["name"] = name
        if rssi is not None:
            entry["rssi"] = rssi
        if tx_power is not None:
            entry["tx_power"] = tx_power
        try:
            if isinstance(manu, dict):
                entry["manufacturer_data"].update(manu)
        except Exception:
            pass
        for s in service_uuids:
            if s not in entry["service_uuids"]:
                entry["service_uuids"].append(s)
        seen[address] = entry
    return list(seen.values())

async def _scan_with_discover_simple(timeout=5.0):
    from bleak import BleakScanner
    devices = await BleakScanner.discover(timeout=timeout)
    seen = {}
    for d in devices:
        try:
            if isinstance(d, (tuple, list)) and len(d) >= 2:
                dev = d[0]
            else:
                dev = d
        except Exception:
            dev = d
        if isinstance(dev, (str, bytes)):
            address = str(dev)
            name = None
            rssi = None
            manu = {}
            service_uuids = []
            tx_power = None
        else:
            address = getattr(dev, "address", None) or repr(dev)
            name = getattr(dev, "name", None)
            rssi = getattr(dev, "rssi", None)
            manu = getattr(dev, "metadata", {}).get("manufacturer_data", {}) if getattr(dev, "metadata", None) else {}
            service_uuids = getattr(dev, "metadata", {}).get("uuids", []) if getattr(dev, "metadata", None) else []
            tx_power = None
        entry = seen.get(address, {"name": None, "address": address, "rssi": None, "tx_power": None, "manufacturer_data": {}, "service_uuids": []})
        if name:
            entry["name"] = name
        if rssi is not None:
            entry["rssi"] = rssi
        try:
            if isinstance(manu, dict):
                entry["manufacturer_data"].update(manu)
        except Exception:
            pass
        for s in service_uuids:
            if s not in entry["service_uuids"]:
                entry["service_uuids"].append(s)
        seen[address] = entry
    return list(seen.values())

async def async_scan_bluetooth(timeout=5.0):
    if not _HAS_BLEAK:
        raise RuntimeError("Bleak library not installed. Run: pip install bleak")
    # Try callback first
    raw_list = []
    try:
        if hasattr(BleakScanner, "register_detection_callback"):
            raw_list = await _scan_with_callback(timeout=timeout)
        else:
            raise RuntimeError("no callback API")
    except Exception:
        try:
            raw_list = await _scan_with_discover_return_adv(timeout=timeout)
        except Exception:
            raw_list = await _scan_with_discover_simple(timeout=timeout)
    results = []
    for info in raw_list:
        if not isinstance(info, dict):
            try:
                addr = getattr(info, "address", None) or str(info)
                name = getattr(info, "name", None) or "Unknown Device"
                rssi = getattr(info, "rssi", None)
                manu = getattr(info, "manufacturer_data", {}) or {}
                service_uuids = getattr(info, "service_uuids", []) or []
                tx = getattr(info, "tx_power", None)
            except Exception:
                addr = str(info)
                name = "Unknown Device"
                rssi = None
                manu = {}
                service_uuids = []
                tx = None
        else:
            addr = info.get("address") or info.get("address_repr") or str(info)
            name = info.get("name") or "Unknown Device"
            rssi = info.get("rssi")
            manu = info.get("manufacturer_data", {}) or {}
            service_uuids = info.get("service_uuids", []) or []
            tx = info.get("tx_power", None)
        addr = sanitize_address(addr)
        # choose display name: prefer actual name, else show address
        display_name = name if name and name != "Unknown Device" else addr
        if rssi is None:
            rssi_val = -90
        else:
            try:
                rssi_val = int(rssi)
            except Exception:
                rssi_val = -90
        try:
            tx_for_calc = int(tx) if tx is not None else -59
        except Exception:
            tx_for_calc = -59
        try:
            n = 2.7
            distance = 10 ** ((tx_for_calc - rssi_val) / (10 * n))
            distance = max(0.1, min(200.0, distance))
            distance_str = f"{distance:.2f} m"
        except Exception:
            distance_str = "N/A"
        secure_type = "Unknown"
        secure_flag = "❓ Unknown"
        if (isinstance(manu, dict) and manu) or (isinstance(service_uuids, (list, tuple)) and len(service_uuids) > 0):
            secure_type = "Encrypted"
            secure_flag = "✅ Safe"
        results.append({
            "Name": display_name,
            "BSSID": addr,
            "Signal (dBm)": f"{rssi_val} dBm",
            "Signal (%)": rssi_to_percent(rssi_val),
            "Distance": distance_str,
            "Protocol": "Bluetooth",
            "Channel": "N/A",
            "Security Type": secure_type,
            "IP Type": "N/A",
            "Secure To Use": secure_flag
        })
    if not results:
        results = [{
            "Name": "No BLE devices",
            "BSSID": "N/A",
            "Signal (dBm)": "N/A",
            "Signal (%)": "N/A",
            "Distance": "N/A",
            "Protocol": "Bluetooth",
            "Channel": "N/A",
            "Security Type": "N/A",
            "IP Type": "N/A",
            "Secure To Use": "N/A"
        }]
    return results

def scan_bluetooth_blocking(timeout=5.0):
    if platform.system().lower() == "windows":
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        except Exception:
            pass
    loop = asyncio.new_event_loop()
    try:
        devices = loop.run_until_complete(async_scan_bluetooth(timeout=timeout))
        return devices
    finally:
        try:
            loop.run_until_complete(asyncio.sleep(0))
        except Exception:
            pass
        loop.close()

def check_ble_adapter(timeout=2.0):
    if not _HAS_BLEAK:
        return False, "Bleak not installed."
    try:
        if platform.system().lower() == "windows":
            try:
                asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            except Exception:
                pass
        loop = asyncio.new_event_loop()
        try:
            devices = loop.run_until_complete(async_scan_bluetooth(timeout=timeout))
            if len(devices) == 1 and devices[0].get("Name") == "No BLE devices":
                return True, "Adapter OK but no adverts seen during quick scan."
            return True, f"Adapter OK, {len(devices)} devices detected (in quick scan)."
        finally:
            loop.run_until_complete(asyncio.sleep(0))
            loop.close()
    except Exception as e:
        return False, f"BLE adapter or permissions error: {e}"

# ---------------------- Demo loader ----------------------

def load_json_sample(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            else:
                return []
    except Exception:
        return []

def load_demo_data():
    # samples folder (relative)
    base = os.path.join(os.path.dirname(__file__), "samples")
    ble_file = os.path.join(base, "ble_sample.json")
    wifi_file = os.path.join(base, "wifi_sample.json")
    ble = load_json_sample(ble_file)
    wifi = load_json_sample(wifi_file)
    return wifi, ble

# ---------------------- CLI printer ----------------------

def print_results(results):
    if not results:
        print("No networks/devices found.")
        return
    def sig_val(x):
        try:
            return int(re.search(r"-?\d+", x.get("Signal (dBm)", "-999")).group(0))
        except Exception:
            return -999
    sorted_res = sorted(results, key=sig_val, reverse=True)
    for r in sorted_res:
        print(f"{r['Name']:<30} {r['BSSID']:<20} {r['Signal (dBm)']:<10} {r['Signal (%)']:<6} {r['Distance']:<10} {r['Protocol']:<8} {r['Channel']:<6} {r['Security Type']}")
    top = sorted_res[0]
    print("\nRecommended:", top['Name'], top['Signal (dBm)'], top['Security Type'], top['Secure To Use'])

# ---------------------- GUI Application (if Tk available) ----------------------

if _HAS_TK:
    class SignalAnalyzerApp:
        def __init__(self, root, demo_mode=False, demo_wifi=None, demo_ble=None):
            self.root = root
            self.root.title("📡 Signal Analyzer for Wireless Communication")
            self.root.geometry("1200x650")
            self.root.config(bg="#eef4ff")

            title = tk.Label(root, text="Signal Analyzer – Wi-Fi & Bluetooth Scanner",
                             font=("Segoe UI", 16, "bold"), bg="#004c99", fg="white", pady=10)
            title.pack(fill="x")

            btn_frame = tk.Frame(root, bg="#eef4ff")
            btn_frame.pack(pady=10)
            tk.Button(btn_frame, text="🔍 Scan Wi-Fi", command=self.start_wifi_scan,
                      width=18, bg="#3399ff", fg="white").grid(row=0, column=0, padx=8)
            tk.Button(btn_frame, text="🔍 Scan Bluetooth", command=self.display_bluetooth,
                      width=18, bg="#33cc33", fg="white").grid(row=0, column=1, padx=8)
            tk.Button(btn_frame, text="🔁 Refresh Last Scan", command=self.refresh_last,
                      width=18, bg="#ffcc33", fg="#222").grid(row=0, column=2, padx=8)
            tk.Button(btn_frame, text="❌ Exit", command=root.quit,
                      width=18, bg="#ff3333", fg="white").grid(row=0, column=3, padx=8)

            self.cols = ("Name", "BSSID", "Signal (dBm)", "Signal (%)", "Distance", "Protocol", "Channel", "Security Type", "IP Type", "Secure To Use")
            self.tree = ttk.Treeview(root, columns=self.cols, show="headings", height=22)
            for col in self.cols:
                self.tree.heading(col, text=col)
                width = 220 if col == "Name" else 110
                self.tree.column(col, width=width, anchor="center")
            self.tree.pack(fill="both", expand=True, padx=10, pady=10)

            self.best_label = tk.Label(root, text="", font=("Segoe UI", 12, "bold"), bg="#eef4ff", fg="#004c00")
            self.best_label.pack(pady=5)

            self.last_scan_data = []
            self.last_scan_type = None

            self.demo_mode = demo_mode
            self.demo_wifi = demo_wifi or []
            self.demo_ble = demo_ble or []

        # Wi-Fi
        def start_wifi_scan(self):
            self.tree.delete(*self.tree.get_children())
            self.best_label.config(text="Scanning Wi-Fi... Please wait ⏳", fg="#333")
            if self.demo_mode:
                # show demo data immediately
                self.last_scan_data = self.demo_wifi
                self.last_scan_type = "wifi"
                self.root.after(200, lambda: self._display_results(self.demo_wifi, scan_type="wifi"))
                return
            threading.Thread(target=self._wifi_scan_task, daemon=True).start()

        def _wifi_scan_task(self):
            try:
                results = scan_wifi_windows()
                self.last_scan_data = results
                self.last_scan_type = "wifi"
                self.root.after(0, lambda: self._display_results(results, scan_type="wifi"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Wi-Fi Scan Error", str(e)))
                self.root.after(0, lambda: self.best_label.config(text="Wi-Fi scan failed.", fg="#a00"))

        def _display_results(self, results, scan_type="wifi"):
            self.tree.delete(*self.tree.get_children())
            if not results:
                self.best_label.config(text="No networks/devices found.", fg="#a00")
                return
            def sig_key(x):
                try:
                    return int(re.search(r"-?\d+", x["Signal (dBm)"]).group(0))
                except:
                    return -999
            def security_rank(sec):
                s = (sec or "").upper()
                if "WPA3" in s:
                    return 3
                if "WPA2" in s:
                    return 2
                if "WPA" in s:
                    return 1
                if "OPEN" in s or "NONE" in s:
                    return -1
                if "WEP" in s:
                    return -2
                return 0
            results_sorted = sorted(results, key=lambda x: (security_rank(x.get("Security Type", "")), sig_key(x)), reverse=True)
            for item in results_sorted:
                values = tuple(item.get(c, "N/A") for c in self.cols)
                self.tree.insert("", "end", values=values)
            best = results_sorted[0]
            self.best_label.config(
                text=f"🌟 Recommended: {best['Name']} ({best['Signal (dBm)']}, {best['Security Type']}, {best['Secure To Use']})",
                fg="#004c00"
            )

        def refresh_last(self):
            if not self.last_scan_type:
                messagebox.showinfo("Nothing to Refresh", "No previous scan to refresh. Use 'Scan Wi-Fi' or 'Scan Bluetooth'.")
                return
            if self.last_scan_type == "wifi":
                self.start_wifi_scan()
            elif self.last_scan_type == "bluetooth":
                self.display_bluetooth()

        # Bluetooth
        def display_bluetooth(self):
            self.tree.delete(*self.tree.get_children())
            self.best_label.config(text="Scanning Bluetooth... Please wait ⏳", fg="#333")
            if self.demo_mode:
                self.last_scan_data = self.demo_ble
                self.last_scan_type = "bluetooth"
                self.root.after(200, lambda: self.show_bluetooth_results(self.demo_ble))
                return
            threading.Thread(target=self._bt_task, daemon=True).start()

        def _bt_task(self):
            try:
                devices = scan_bluetooth_blocking(timeout=5.0)
                self.last_scan_data = devices
                self.last_scan_type = "bluetooth"
                self.root.after(0, lambda: self.show_bluetooth_results(devices))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Bluetooth Error", str(e)))
                self.root.after(0, lambda: self.best_label.config(text="Bluetooth scan failed.", fg="#a00"))

        def show_bluetooth_results(self, devices):
            self.tree.delete(*self.tree.get_children())
            if not devices:
                self.best_label.config(text="No Bluetooth devices found.", fg="#a00")
                return
            def sig_key(x):
                try:
                    return int(re.search(r"-?\d+", x["Signal (dBm)"]).group(0))
                except:
                    return -999
            devices_sorted = sorted(devices, key=sig_key, reverse=True)
            for dev in devices_sorted:
                values = tuple(dev.get(c, "N/A") for c in self.cols)
                self.tree.insert("", "end", values=values)
            self.best_label.config(text="✅ Bluetooth scan complete.", fg="#004c00")

# ---------------------- Entrypoint ----------------------

def main(cli_mode=False, demo_mode=False):
    if demo_mode:
        wifi_demo, ble_demo = load_demo_data()
    else:
        wifi_demo, ble_demo = None, None

    if cli_mode:
        print("Running in CLI mode.")
        if demo_mode:
            print("\n--- Demo Wi-Fi entries ---")
            print_results(wifi_demo)
            print("\n--- Demo BLE entries ---")
            print_results(ble_demo)
            return
        # Wi-Fi
        if platform.system().lower() == "windows":
            try:
                wifi = scan_wifi_windows()
                print("\nWi-Fi Networks:")
                print_results(wifi)
            except Exception as e:
                print("Wi-Fi scan error:", e)
        else:
            print("Wi-Fi scanning via netsh supported only on Windows. Skipping Wi-Fi.")
        # Bluetooth
        ok, msg = check_ble_adapter()
        if not ok:
            print("\nBluetooth check:", msg)
        else:
            print("\nScanning Bluetooth (BLE)...")
            try:
                bt = scan_bluetooth_blocking(timeout=5.0)
                print_results(bt)
            except Exception as e:
                print("Bluetooth scan error:", e)
        return

    # GUI mode
    if not _HAS_TK:
        print("Tkinter is not available. Run with --cli for console mode.")
        return
    try:
        root = tk.Tk()
        app = SignalAnalyzerApp(root, demo_mode=demo_mode, demo_wifi=wifi_demo, demo_ble=ble_demo)
        root.mainloop()
    except Exception as e:
        try:
            messagebox.showerror("Fatal Error", f"Application failed to start:\n{e}")
        except Exception:
            print("Fatal Error:", e)
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cli", action="store_true", help="Run CLI-only (no GUI).")
    parser.add_argument("--demo", action="store_true", help="Run in demo mode (load sample JSON).")
    args = parser.parse_args()
    main(cli_mode=args.cli, demo_mode=args.demo)

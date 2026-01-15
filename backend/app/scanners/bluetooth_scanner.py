"""
bluetooth_scanner.py
--------------------
Clean Bluetooth (BLE) scanner with device-centric parameters.
Used by FastAPI backend via scanner_adapter.
"""

import asyncio
import platform
from collections import defaultdict

try:
    from bleak import BleakScanner
    _HAS_BLEAK = True
except Exception:
    _HAS_BLEAK = False


BLE_SEEN = defaultdict(int)


def classify_ble_device(name: str) -> str:
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


def ble_stability(count: int) -> str:
    if count >= 3:
        return "Stable"
    if count == 2:
        return "Medium"
    return "Highly Random"


def scan_bluetooth_blocking(timeout: int = 5, rounds: int = 3):
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

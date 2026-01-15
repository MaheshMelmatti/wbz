"""
scanner_adapter.py
-------------------
Stable adapter layer between FastAPI routes and
Wi-Fi / Bluetooth scanner implementations.

❗ This file must NOT contain scanning logic.
It only safely invokes scanner modules in background threads.
"""

import asyncio
import traceback
from typing import List, Dict, Any

from app.scanners.wifi_scanner import scan_wifi_windows
from app.scanners.bluetooth_scanner import scan_bluetooth_blocking
from app.scanners.zigbee_scanner import scan_zigbee_networks


# ------------------ WI-FI ------------------

async def scan_wifi_once() -> List[Dict[str, Any]]:
    """
    Run one Wi-Fi scan asynchronously.
    """
    try:
        results = await asyncio.to_thread(scan_wifi_windows)

        if not isinstance(results, list):
            return [{"error": "Wi-Fi scanner returned invalid data"}]

        return results

    except Exception as e:
        print("❌ Wi-Fi Scan Error:", e)
        traceback.print_exc()
        return [{
            "error": "Wi-Fi scan failed",
            "details": str(e)
        }]


# ------------------ BLUETOOTH ------------------

async def scan_ble_once(timeout: int = 5, rounds: int = 3) -> List[Dict[str, Any]]:
    """
    Run one Bluetooth (BLE) scan asynchronously.

    timeout: seconds per scan round
    rounds: number of scan passes to improve stability
    """
    try:
        results = await asyncio.to_thread(
            scan_bluetooth_blocking,
            timeout,
            rounds
        )

        if not isinstance(results, list):
            return [{"error": "Bluetooth scanner returned invalid data"}]

        return results

    except Exception as e:
        print("❌ Bluetooth Scan Error:", e)
        traceback.print_exc()
        return [{
            "error": "Bluetooth scan failed",
            "details": str(e)
        }]

# ------------------ ZIGBEE ------------------

async def scan_zigbee_once() -> List[Dict[str, Any]]:
    """
    Run one Zigbee scan asynchronously.
    """
    try:
        results = await asyncio.to_thread(scan_zigbee_networks)

        if not isinstance(results, list):
            return [{"error": "Zigbee scanner returned invalid data"}]

        return results

    except Exception as e:
        print("❌ Zigbee Scan Error:", e)
        traceback.print_exc()
        return [{
            "error": "Zigbee scan failed",
            "details": str(e)
        }]

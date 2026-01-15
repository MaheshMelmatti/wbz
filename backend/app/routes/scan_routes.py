from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import traceback

from app.scanner_adapter import scan_wifi_once, scan_ble_once, scan_zigbee_once

router = APIRouter(prefix="/api/scan", tags=["scan"])


@router.get("/wifi")
async def scan_wifi() -> List[Dict[str, Any]]:
    """
    One-shot Wi-Fi scan.
    Runs blocking scanner safely via scanner_adapter.
    """
    try:
        results = await scan_wifi_once()

        if not isinstance(results, list):
            return [{"error": "Wi-Fi scanner returned invalid data"}]

        return results

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail="Wi-Fi scan failed"
        )


@router.get("/ble")
async def scan_ble() -> List[Dict[str, Any]]:
    """
    One-shot Bluetooth (BLE) scan.
    """
    try:
        results = await scan_ble_once()

        if not isinstance(results, list):
            return [{"error": "BLE scanner returned invalid data"}]

        return results

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail="BLE scan failed"
        )

@router.get("/zigbee")
async def scan_zigbee() -> List[Dict[str, Any]]:
    """
    One-shot Zigbee scan.
    """
    try:
        results = await scan_zigbee_once()

        if not isinstance(results, list):
            return [{"error": "Zigbee scanner returned invalid data"}]

        return results

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail="Zigbee scan failed"
        )

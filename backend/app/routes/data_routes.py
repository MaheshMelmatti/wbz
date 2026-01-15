from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from bson import ObjectId

from app.auth import get_current_user
from app.mongo import scans_collection

router = APIRouter(prefix="/api/data", tags=["data"])


# ------------------ MODELS ------------------

class SaveScanRequest(BaseModel):
    name: Optional[str] = None
    items: Optional[List[Dict]] = None
    raw_json: Optional[Any] = None
    kind: Optional[str] = "wifi"  # wifi | bluetooth


# ------------------ SAVE SCAN ------------------

@router.post("/save")
async def save_scan(payload: SaveScanRequest, current_user=Depends(get_current_user)):
    raw = payload.items or payload.raw_json
    if not raw or not isinstance(raw, list):
        raise HTTPException(status_code=400, detail="Invalid scan data")

    doc = {
        "user_id": current_user.id,
        "name": payload.name or f"Scan {datetime.utcnow().isoformat()}",
        "kind": payload.kind or "wifi",          # ✅ FIX
        "items": raw,
        "count": len(raw),
        "created_at": datetime.utcnow(),          # stored as UTC
    }

    result = scans_collection.insert_one(doc)

    return {
        "id": str(result.inserted_id),
        "count": doc["count"],
        "kind": doc["kind"],
        "timestamp": doc["created_at"].isoformat(),
    }


# ------------------ LIST SCANS ------------------

@router.get("/list")
def list_scans(current_user=Depends(get_current_user)):
    scans = scans_collection.find(
        {"user_id": current_user.id},
        {"items": 0}
    ).sort("created_at", -1)

    return [
        {
            "id": str(s["_id"]),
            "name": s.get("name"),
            "kind": s.get("kind", "wifi"),          # ✅ FIX
            "count": s.get("count"),
            "timestamp": s.get("created_at").isoformat(),
        }
        for s in scans
    ]


# ------------------ GET SINGLE SCAN ------------------

@router.get("/{scan_id}")
def get_scan(scan_id: str, current_user=Depends(get_current_user)):
    try:
        oid = ObjectId(scan_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid scan ID")

    scan = scans_collection.find_one({
        "_id": oid,
        "user_id": current_user.id
    })

    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    return {
        "id": str(scan["_id"]),
        "name": scan["name"],
        "kind": scan.get("kind", "wifi"),          # ✅ FIX
        "timestamp": scan["created_at"].isoformat(),
        "count": scan["count"],
        "items": scan["items"],
    }


# ------------------ DELETE SCAN ------------------

@router.delete("/{scan_id}")
def delete_scan(scan_id: str, current_user=Depends(get_current_user)):
    try:
        oid = ObjectId(scan_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid scan ID")

    res = scans_collection.delete_one({
        "_id": oid,
        "user_id": current_user.id
    })

    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Scan not found")

    return {"deleted": True}


# ------------------ DOWNLOAD SCAN ------------------

@router.get("/{scan_id}/download", response_class=HTMLResponse)
def download_scan_html(scan_id: str, current_user=Depends(get_current_user)):
    try:
        oid = ObjectId(scan_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid scan ID")

    scan = scans_collection.find_one({
        "_id": oid,
        "user_id": current_user.id
    })

    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    items = scan.get("items", [])
    kind = scan.get("kind", "wifi")

    # ----- IST TIME FIX -----
    created_utc = scan["created_at"].replace(tzinfo=timezone.utc)
    ist = timezone(timedelta(hours=5, minutes=30))
    created = created_utc.astimezone(ist).strftime("%d %b %Y, %I:%M:%S %p")

    # ----- TABLE HEADERS -----
    if kind == "bluetooth":
        headers = """
        <tr>
          <th>#</th>
          <th>Device Name</th>
          <th>Device ID</th>
          <th>Proximity (%)</th>
          <th>Category</th>
          <th>Stability</th>
          <th>Pairing</th>
        </tr>
        """
    elif kind == "zigbee":
        headers = """
        <tr>
          <th>#</th>
          <th>Device Name</th>
          <th>IEEE Address</th>
          <th>Network Addr</th>
          <th>RSSI</th>
          <th>LQI</th>
          <th>Distance</th>
          <th>PAN ID</th>
          <th>Channel</th>
          <th>Device Type</th>
          <th>Security</th>
          <th>Battery</th>
        </tr>
        """
    else:
        headers = """
        <tr>
          <th>#</th>
          <th>SSID</th>
          <th>BSSID</th>
          <th>Signal (dBm)</th>
          <th>Signal %</th>
          <th>Channel</th>
          <th>Distance</th>
          <th>Security</th>
        </tr>
        """

    rows = []
    for i, it in enumerate(items, 1):
        if kind == "bluetooth":
            rows.append(f"""
            <tr>
              <td>{i}</td>
              <td>{it.get("Device Name","")}</td>
              <td>{it.get("Device ID","")}</td>
              <td>{it.get("Proximity (%)","")}</td>
              <td>{it.get("Device Category","")}</td>
              <td>{it.get("Advertised Stability","")}</td>
              <td>{it.get("Pairing Required","")}</td>
            </tr>
            """)
        elif kind == "zigbee":
            rows.append(f"""
            <tr>
              <td>{i}</td>
              <td>{it.get("Name","")}</td>
              <td>{it.get("IEEE Address","")}</td>
              <td>{it.get("Network Address","")}</td>
              <td>{it.get("RSSI","")}</td>
              <td>{it.get("LQI","")}</td>
              <td>{it.get("Distance","")}</td>
              <td>{it.get("PAN ID","")}</td>
              <td>{it.get("Channel","")}</td>
              <td>{it.get("Device Type","")}</td>
              <td>{it.get("Security","")}</td>
              <td>{it.get("Battery Level","")}</td>
            </tr>
            """)
        else:
            rows.append(f"""
            <tr>
              <td>{i}</td>
              <td>{it.get("Name","")}</td>
              <td>{it.get("BSSID","")}</td>
              <td>{it.get("Signal (dBm)","")}</td>
              <td>{it.get("Signal (%)","")}</td>
              <td>{it.get("Channel","")}</td>
              <td>{it.get("Distance","")}</td>
              <td>{it.get("Security Type","")}</td>
            </tr>
            """)

    html = f"""
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Signal Analyzer — Scan Report</title>
<style>
body{{font-family:Arial;margin:32px}}
table{{width:100%;border-collapse:collapse}}
th,td{{padding:10px;border-bottom:1px solid #ddd}}
th{{background:#f3f4f6}}
</style>
</head>
<body>
<h1>📡 Signal Analyzer — {kind.capitalize()} Scan</h1>
<p>Generated: {created} (IST)</p>

<table>
<thead>{headers}</thead>
<tbody>{"".join(rows)}</tbody>
</table>

<p style="margin-top:20px;color:#666">Generated by Signal Analyzer</p>
</body>
</html>
"""

    return html

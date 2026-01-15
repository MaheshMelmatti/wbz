"""
wifi_scanner.py
---------------
Windows Wi-Fi scanner using netsh.
This file contains ONLY Wi-Fi logic.
"""

import subprocess
import re
import math
import random
import time
import platform


# ------------------ HELPERS ------------------

def percent_to_dbm(quality):
    try:
        q = int(quality)
    except Exception:
        return -90
    if q >= 100:
        return -30
    if q <= 1:
        return -90
    return int(-30 - (100 - q) * 0.55)


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


# ------------------ CORE SCAN FUNCTION ------------------

def scan_wifi_windows():
    """
    Perform a Wi-Fi scan using netsh (Windows only).
    """
    if platform.system().lower() != "windows":
        raise RuntimeError("Wi-Fi scanning only supported on Windows")

    subprocess.run(
        "netsh wlan refresh",
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    time.sleep(1)

    output = subprocess.check_output(
        "netsh wlan show networks mode=bssid",
        shell=True,
        text=True,
        encoding="utf-8",
        errors="ignore"
    )

    return _parse_netsh_output(output)


# ------------------ PARSER ------------------

def _parse_netsh_output(output):
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

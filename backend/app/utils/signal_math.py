import math

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

    pct = int((r + 90) / 60 * 100)
    return f"{pct}%"


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
        exponent = (
            27.55
            - (20 * math.log10(freq_mhz))
            + abs(float(rssi_dbm))
        ) / 20.0

        distance = 10 ** exponent
        return f"{max(0.2, min(500.0, distance)):.2f} m"
    except Exception:
        return "N/A"


def get_band(freq_mhz):
    if freq_mhz < 3000:
        return "2.4 GHz"
    if freq_mhz < 6000:
        return "5 GHz"
    return "6+ GHz"

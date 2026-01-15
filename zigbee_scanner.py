import random
import math
import time
import json
import os

def estimate_distance(rssi, freq_mhz=2400):
    """
    Estimate distance using log-distance path loss model for Zigbee (2.4 GHz).
    """
    try:
        tx_power = -25  # Typical Zigbee transmit power
        n = 3.5  # Path loss exponent for indoor Zigbee
        if freq_mhz > 900:  # 2.4 GHz
            n = 3.5
        else:  # Sub-GHz
            n = 2.8

        distance = 10 ** ((tx_power - rssi) / (10 * n))
        return f"{min(max(distance, 0.1), 100):.2f} m"
    except:
        return "N/A"

def generate_zigbee_device(device_id, pan_id="0x1A2B", channel=15):
    """
    Generate a realistic Zigbee device entry.
    """
    device_types = ["Coordinator", "Router", "End Device", "Sleepy End Device"]
    manufacturers = ["Texas Instruments", "NXP", "Silicon Labs", "Unknown"]
    device_names = [
        "Smart Light", "Temperature Sensor", "Door Sensor", "Motion Detector",
        "Smart Plug", "Thermostat", "Smoke Detector", "Gateway", "Router Node"
    ]

    # Generate IEEE address
    ieee_base = "00:12:4B:00"
    random_part = ":".join([f"{random.randint(0, 255):02X}" for _ in range(4)])
    ieee_addr = f"{ieee_base}:{random_part}"

    # Generate network address
    network_addr = f"0x{random.randint(0, 65535):04X}"

    # Generate RSSI
    rssi = random.randint(-85, -45)

    # Random device type
    device_type = random.choice(device_types)

    # Random manufacturer
    manufacturer = random.choice(manufacturers)

    # Random device name
    device_name = f"{random.choice(device_names)}_{device_id:02d}"

    # Security status
    security = random.choice(["Enabled", "Disabled", "Pre-configured"])

    # LQI (Link Quality Indicator)
    lqi = random.randint(0, 255)

    # Battery level (for end devices)
    battery = random.randint(10, 100) if "End Device" in device_type else "N/A"

    return {
        "Device Name": device_name,
        "IEEE Address": ieee_addr,
        "Network Address": network_addr,
        "RSSI (dBm)": str(rssi),
        "LQI": str(lqi),
        "Distance": estimate_distance(rssi),
        "PAN ID": pan_id,
        "Channel": str(channel),
        "Device Type": device_type,
        "Manufacturer": manufacturer,
        "Security": security,
        "Battery Level": f"{battery}%" if battery != "N/A" else battery,
        "Last Seen": time.strftime("%H:%M:%S")
    }

def scan_zigbee_networks(channels=None, timeout=3.0):
    """
    Simulate Zigbee network discovery across multiple channels.
    """
    if channels is None:
        channels = [11, 15, 20, 25]  # Common Zigbee channels

    time.sleep(timeout)  # Simulate scan delay

    networks = []
    device_count = random.randint(3, 12)

    for i in range(device_count):
        channel = random.choice(channels)
        pan_id = f"0x{random.randint(0, 65535):04X}"
        device = generate_zigbee_device(i + 1, pan_id, channel)
        networks.append(device)

    return networks

def analyze_zigbee_network(devices):
    """
    Analyze Zigbee network topology and provide insights.
    """
    if not devices:
        return {}

    # Group devices by PAN ID
    pan_groups = {}
    for device in devices:
        pan_id = device.get("PAN ID", "Unknown")
        if pan_id not in pan_groups:
            pan_groups[pan_id] = []
        pan_groups[pan_id].append(device)

    analysis = {
        "total_devices": len(devices),
        "networks_found": len(pan_groups),
        "coordinators": len([d for d in devices if d.get("Device Type") == "Coordinator"]),
        "routers": len([d for d in devices if d.get("Device Type") == "Router"]),
        "end_devices": len([d for d in devices if "End Device" in d.get("Device Type", "")]),
        "channels_used": list(set([d.get("Channel") for d in devices if d.get("Channel")])),
        "security_enabled": len([d for d in devices if d.get("Security") == "Enabled"]),
        "manufacturers": list(set([d.get("Manufacturer") for d in devices if d.get("Manufacturer") != "Unknown"]))
    }

    return analysis

def save_scan_results(devices, filename="zigbee_scan_results.json"):
    """
    Save scan results to JSON file.
    """
    try:
        with open(filename, 'w') as f:
            json.dump({
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "devices": devices,
                "analysis": analyze_zigbee_network(devices)
            }, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving results: {e}")
        return False

def load_scan_results(filename="zigbee_scan_results.json"):
    """
    Load previous scan results from JSON file.
    """
    try:
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                data = json.load(f)
            return data
        return None
    except Exception as e:
        print(f"Error loading results: {e}")
        return None

# Legacy function for backward compatibility
def scan_zigbee():
    """
    Simple Zigbee network discovery simulation.
    Returns a basic list of devices.
    """
    return scan_zigbee_networks()

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import random
import json
import os
from zigbee_scanner import scan_zigbee_networks, analyze_zigbee_network, save_scan_results, load_scan_results

class ZigbeeAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🌐 Zigbee Network Analyzer")
        self.root.geometry("1400x800")
        self.root.config(bg="#f0f8ff")

        # Initialize data
        self.scan_data = []
        self.analysis_data = {}
        self.monitoring_active = False

        self.setup_ui()

    def setup_ui(self):
        # Title
        title = tk.Label(
            self.root,
            text="🌐 Zigbee Network Analyzer - IoT Device Scanner",
            font=("Segoe UI", 18, "bold"),
            bg="#2e5c8a",
            fg="white",
            pady=15
        )
        title.pack(fill="x")

        # Control Panel
        control_frame = tk.Frame(self.root, bg="#f0f8ff", pady=10)
        control_frame.pack(fill="x")

        # Scan Controls
        scan_frame = tk.LabelFrame(control_frame, text="Network Scanning", bg="#f0f8ff", padx=10, pady=5)
        scan_frame.pack(side="left", padx=10)

        tk.Button(scan_frame, text="🔍 Quick Scan", command=self.quick_scan,
                 bg="#4CAF50", fg="white", width=15).grid(row=0, column=0, padx=5, pady=5)
        tk.Button(scan_frame, text="🔍 Full Scan", command=self.full_scan,
                 bg="#2196F3", fg="white", width=15).grid(row=0, column=1, padx=5, pady=5)
        tk.Button(scan_frame, text="📊 Analyze Network", command=self.analyze_network,
                 bg="#FF9800", fg="white", width=15).grid(row=0, column=2, padx=5, pady=5)

        # Monitoring Controls
        monitor_frame = tk.LabelFrame(control_frame, text="Real-time Monitoring", bg="#f0f8ff", padx=10, pady=5)
        monitor_frame.pack(side="left", padx=10)

        self.monitor_btn = tk.Button(monitor_frame, text="▶️ Start Monitor", command=self.toggle_monitoring,
                                    bg="#9C27B0", fg="white", width=15)
        self.monitor_btn.grid(row=0, column=0, padx=5, pady=5)

        tk.Button(monitor_frame, text="⏹️ Stop Monitor", command=self.stop_monitoring,
                 bg="#F44336", fg="white", width=15).grid(row=0, column=1, padx=5, pady=5)

        # File Operations
        file_frame = tk.LabelFrame(control_frame, text="File Operations", bg="#f0f8ff", padx=10, pady=5)
        file_frame.pack(side="left", padx=10)

        tk.Button(file_frame, text="💾 Save Results", command=self.save_results,
                 bg="#607D8B", fg="white", width=15).grid(row=0, column=0, padx=5, pady=5)
        tk.Button(file_frame, text="📂 Load Results", command=self.load_results,
                 bg="#795548", fg="white", width=15).grid(row=0, column=1, padx=5, pady=5)

        # Status Bar
        self.status_label = tk.Label(self.root, text="Ready to scan Zigbee networks...",
                                    font=("Segoe UI", 10), bg="#f0f8ff", fg="#333")
        self.status_label.pack(pady=5)

        # Main Content Area
        content_frame = tk.Frame(self.root, bg="#f0f8ff")
        content_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Left Panel - Device List
        left_frame = tk.Frame(content_frame, bg="#f0f8ff")
        left_frame.pack(side="left", fill="both", expand=True)

        tk.Label(left_frame, text="📋 Discovered Devices", font=("Segoe UI", 12, "bold"),
                bg="#f0f8ff").pack(pady=5)

        # Device Table
        columns = ("Device Name", "IEEE Address", "Network Address", "RSSI", "LQI", "Distance",
                  "PAN ID", "Channel", "Device Type", "Security", "Battery")
        self.device_tree = ttk.Treeview(left_frame, columns=columns, show="headings", height=20)

        for col in columns:
            self.device_tree.heading(col, text=col)
            width = 120 if col in ["Device Name", "IEEE Address"] else 80
            self.device_tree.column(col, width=width, anchor="center")

        # Scrollbars for device table
        device_scrollbar_y = ttk.Scrollbar(left_frame, orient="vertical", command=self.device_tree.yview)
        device_scrollbar_x = ttk.Scrollbar(left_frame, orient="horizontal", command=self.device_tree.xview)
        self.device_tree.configure(yscrollcommand=device_scrollbar_y.set, xscrollcommand=device_scrollbar_x.set)

        self.device_tree.pack(side="left", fill="both", expand=True)
        device_scrollbar_y.pack(side="right", fill="y")
        device_scrollbar_x.pack(side="bottom", fill="x")

        # Right Panel - Analysis & Details
        right_frame = tk.Frame(content_frame, bg="#f0f8ff", width=400)
        right_frame.pack(side="right", fill="y", padx=(10, 0))

        # Network Analysis
        analysis_frame = tk.LabelFrame(right_frame, text="📊 Network Analysis", bg="#f0f8ff", padx=10, pady=5)
        analysis_frame.pack(fill="x", pady=5)

        self.analysis_text = tk.Text(analysis_frame, height=12, width=45, font=("Consolas", 9),
                                    bg="#f8f9fa", wrap="word")
        analysis_scrollbar = ttk.Scrollbar(analysis_frame, command=self.analysis_text.yview)
        self.analysis_text.configure(yscrollcommand=analysis_scrollbar.set)

        self.analysis_text.pack(side="left", fill="both", expand=True)
        analysis_scrollbar.pack(side="right", fill="y")

        # Device Details
        details_frame = tk.LabelFrame(right_frame, text="🔍 Device Details", bg="#f0f8ff", padx=10, pady=5)
        details_frame.pack(fill="both", expand=True, pady=5)

        self.details_text = tk.Text(details_frame, height=15, width=45, font=("Consolas", 9),
                                   bg="#f8f9fa", wrap="word")
        details_scrollbar = ttk.Scrollbar(details_frame, command=self.details_text.yview)
        self.details_text.configure(yscrollcommand=details_scrollbar.set)

        self.details_text.pack(side="left", fill="both", expand=True)
        details_scrollbar.pack(side="right", fill="y")

        # Bind device selection
        self.device_tree.bind("<<TreeviewSelect>>", self.show_device_details)

        # Filter Controls
        filter_frame = tk.Frame(self.root, bg="#f0f8ff", pady=5)
        filter_frame.pack(fill="x")

        tk.Label(filter_frame, text="Filter by Device Type:", bg="#f0f8ff").pack(side="left", padx=5)
        self.filter_var = tk.StringVar(value="All")
        filter_combo = ttk.Combobox(filter_frame, textvariable=self.filter_var,
                                   values=["All", "Coordinator", "Router", "End Device", "Sleepy End Device"],
                                   state="readonly", width=15)
        filter_combo.pack(side="left", padx=5)
        filter_combo.bind("<<ComboboxSelected>>", self.apply_filter)

    def quick_scan(self):
        """Perform a quick Zigbee network scan"""
        self.status_label.config(text="🔍 Performing quick Zigbee network scan...", fg="#2196F3")
        self.root.config(cursor="wait")

        def scan_task():
            try:
                devices = scan_zigbee_networks(channels=[15, 20], timeout=2.0)
                self.root.after(0, lambda: self.display_results(devices))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Scan Error", f"Failed to scan: {e}"))
            finally:
                self.root.after(0, lambda: self.root.config(cursor=""))

        threading.Thread(target=scan_task, daemon=True).start()

    def full_scan(self):
        """Perform a comprehensive Zigbee network scan"""
        self.status_label.config(text="🔍 Performing comprehensive Zigbee network scan...", fg="#2196F3")
        self.root.config(cursor="wait")

        def scan_task():
            try:
                devices = scan_zigbee_networks(channels=[11, 15, 20, 25], timeout=4.0)
                self.root.after(0, lambda: self.display_results(devices))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Scan Error", f"Failed to scan: {e}"))
            finally:
                self.root.after(0, lambda: self.root.config(cursor=""))

        threading.Thread(target=scan_task, daemon=True).start()

    def display_results(self, devices):
        """Display scan results in the device table"""
        self.scan_data = devices
        self.device_tree.delete(*self.device_tree.get_children())

        for device in devices:
            values = (
                device.get("Device Name", "N/A"),
                device.get("IEEE Address", "N/A"),
                device.get("Network Address", "N/A"),
                device.get("RSSI (dBm)", "N/A"),
                device.get("LQI", "N/A"),
                device.get("Distance", "N/A"),
                device.get("PAN ID", "N/A"),
                device.get("Channel", "N/A"),
                device.get("Device Type", "N/A"),
                device.get("Security", "N/A"),
                device.get("Battery Level", "N/A")
            )
            self.device_tree.insert("", "end", values=values)

        self.status_label.config(text=f"✅ Scan complete! Found {len(devices)} Zigbee devices.", fg="#4CAF50")
        self.analyze_network()

    def analyze_network(self):
        """Analyze the current network data"""
        if not self.scan_data:
            self.analysis_text.delete(1.0, "end")
            self.analysis_text.insert(1.0, "No network data available.\nRun a scan first.")
            return

        analysis = analyze_zigbee_network(self.scan_data)

        analysis_text = f"""🌐 Network Analysis Report
{'='*30}

📊 Total Devices: {analysis.get('total_devices', 0)}
🏠 Networks Found: {analysis.get('networks_found', 0)}
👑 Coordinators: {analysis.get('coordinators', 0)}
🔄 Routers: {analysis.get('routers', 0)}
📱 End Devices: {analysis.get('end_devices', 0)}

📻 Channels Used: {', '.join(analysis.get('channels_used', []))}
🔒 Security Enabled: {analysis.get('security_enabled', 0)} devices
🏭 Manufacturers: {', '.join(analysis.get('manufacturers', []))}

Network Topology:
• Coordinators manage network formation
• Routers extend network range and routing
• End Devices are leaf nodes (battery-powered)

Security Status:
{self.get_security_summary(analysis)}
"""
        self.analysis_text.delete(1.0, "end")
        self.analysis_text.insert(1.0, analysis_text)

    def get_security_summary(self, analysis):
        """Generate security summary"""
        total = analysis.get('total_devices', 0)
        secure = analysis.get('security_enabled', 0)

        if total == 0:
            return "No devices found."

        secure_percent = (secure / total) * 100
        if secure_percent >= 80:
            return f"🟢 Good: {secure_percent:.1f}% devices have security enabled"
        elif secure_percent >= 50:
            return f"🟡 Moderate: {secure_percent:.1f}% devices have security enabled"
        else:
            return f"🔴 Poor: Only {secure_percent:.1f}% devices have security enabled"

    def show_device_details(self, event):
        """Show detailed information for selected device"""
        selection = self.device_tree.selection()
        if not selection:
            return

        item = self.device_tree.item(selection[0])
        values = item['values']

        device_info = f"""🔍 Device Information
{'='*25}

Name: {values[0]}
IEEE Address: {values[1]}
Network Address: {values[2]}

Signal Strength:
• RSSI: {values[3]} dBm
• LQI: {values[4]}/255
• Estimated Distance: {values[5]}

Network Info:
• PAN ID: {values[6]}
• Channel: {values[7]}

Device Properties:
• Type: {values[8]}
• Security: {values[9]}
• Battery: {values[10]}

Device Classification:
{self.get_device_classification(values[8])}
"""
        self.details_text.delete(1.0, "end")
        self.details_text.insert(1.0, device_info)

    def get_device_classification(self, device_type):
        """Get detailed device type information"""
        classifications = {
            "Coordinator": "Central controller that forms and manages the Zigbee network. Always powered and handles network security.",
            "Router": "Network router that extends range and provides routing capabilities. Typically mains-powered.",
            "End Device": "Leaf node that communicates only with parent devices. Can be battery-powered and sleep to conserve energy.",
            "Sleepy End Device": "Battery-powered end device that spends most time asleep to maximize battery life."
        }
        return classifications.get(device_type, "Unknown device type.")

    def apply_filter(self, event=None):
        """Apply device type filter"""
        filter_type = self.filter_var.get()

        # Clear current display
        self.device_tree.delete(*self.device_tree.get_children())

        # Filter and display devices
        for device in self.scan_data:
            device_type = device.get("Device Type", "")
            if filter_type == "All" or device_type == filter_type:
                values = (
                    device.get("Device Name", "N/A"),
                    device.get("IEEE Address", "N/A"),
                    device.get("Network Address", "N/A"),
                    device.get("RSSI (dBm)", "N/A"),
                    device.get("LQI", "N/A"),
                    device.get("Distance", "N/A"),
                    device.get("PAN ID", "N/A"),
                    device.get("Channel", "N/A"),
                    device.get("Device Type", "N/A"),
                    device.get("Security", "N/A"),
                    device.get("Battery Level", "N/A")
                )
                self.device_tree.insert("", "end", values=values)

    def toggle_monitoring(self):
        """Toggle real-time network monitoring"""
        if self.monitoring_active:
            self.stop_monitoring()
        else:
            self.start_monitoring()

    def start_monitoring(self):
        """Start real-time network monitoring"""
        self.monitoring_active = True
        self.monitor_btn.config(text="⏸️ Pause Monitor", bg="#FF9800")
        self.status_label.config(text="📡 Monitoring Zigbee network in real-time...", fg="#9C27B0")

        def monitor_task():
            while self.monitoring_active:
                try:
                    # Simulate periodic network updates
                    time.sleep(5)  # Update every 5 seconds

                    if self.monitoring_active:
                        # Add some random device updates
                        if self.scan_data and random.random() < 0.3:  # 30% chance
                            self.simulate_device_update()
                except Exception as e:
                    print(f"Monitoring error: {e}")
                    break

        threading.Thread(target=monitor_task, daemon=True).start()

    def stop_monitoring(self):
        """Stop real-time monitoring"""
        self.monitoring_active = False
        self.monitor_btn.config(text="▶️ Start Monitor", bg="#9C27B0")
        self.status_label.config(text="⏹️ Network monitoring stopped.", fg="#666")

    def simulate_device_update(self):
        """Simulate a device status update"""
        if not self.scan_data:
            return

        # Pick a random device to update
        device_idx = random.randint(0, len(self.scan_data) - 1)
        device = self.scan_data[device_idx]

        # Update RSSI slightly
        current_rssi = int(device.get("RSSI (dBm)", "-60"))
        new_rssi = current_rssi + random.randint(-5, 5)
        new_rssi = max(-90, min(-30, new_rssi))
        device["RSSI (dBm)"] = str(new_rssi)
        device["Distance"] = device["Distance"]  # Would recalculate distance

        # Update battery for end devices
        if "End Device" in device.get("Device Type", "") and device.get("Battery Level") != "N/A":
            current_battery = int(device["Battery Level"].rstrip("%"))
            new_battery = max(0, current_battery + random.randint(-2, 1))
            device["Battery Level"] = f"{new_battery}%"

        # Update timestamp
        device["Last Seen"] = time.strftime("%H:%M:%S")

        # Refresh display
        self.root.after(0, self.apply_filter)

    def save_results(self):
        """Save scan results to file"""
        if not self.scan_data:
            messagebox.showwarning("No Data", "No scan data to save. Run a scan first.")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Save Zigbee Scan Results"
        )

        if filename:
            try:
                success = save_scan_results(self.scan_data, filename)
                if success:
                    messagebox.showinfo("Success", f"Results saved to {filename}")
                else:
                    messagebox.showerror("Error", "Failed to save results.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save: {e}")

    def load_results(self):
        """Load scan results from file"""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Load Zigbee Scan Results"
        )

        if filename:
            try:
                data = load_scan_results(filename)
                if data and "devices" in data:
                    self.display_results(data["devices"])
                    messagebox.showinfo("Success", f"Results loaded from {filename}")
                else:
                    messagebox.showerror("Error", "Invalid file format.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load: {e}")

def main():
    root = tk.Tk()
    app = ZigbeeAnalyzerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
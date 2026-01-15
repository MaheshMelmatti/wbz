import { useEffect, useState } from "react";
import ScanControl from "./components/ScanControl";
import NetworksTable from "./components/NetworksTable";
import SignalChart from "./components/SignalChart";
import BluetoothChart from "./components/BluetoothChart";
import LoginModal from "./components/LoginModal";
import SavedScansPanel from "./components/SavedScansPanel";

import {
  me,
  saveScan,
  listScans,
  deleteScan,
  downloadScan,
} from "./services/api";

export default function App() {
  const [results, setResults] = useState([]);
  const [status, setStatus] = useState("Idle");
  const [isScanning, setIsScanning] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(null);

  // ✅ scan mode
  const [scanType, setScanType] = useState(null); // "wifi" | "ble" | "zigbee"


  /* ---------- AUTH ---------- */
  const [token, setToken] = useState(() =>
    localStorage.getItem("sa_token")
  );
  const [user, setUser] = useState(null);
  const [loginOpen, setLoginOpen] = useState(false);

  /* ---------- SAVED SCANS ---------- */
  const [savedScans, setSavedScans] = useState([]);

  /* ---------- LOAD USER + SAVED SCANS ---------- */
  useEffect(() => {
    if (!token) return;

    me(token)
      .then((u) => {
        if (u?.detail) throw new Error();
        setUser(u);
        return listScans(token);
      })
      .then((scans) => {
        setSavedScans(scans || []);
      })
      .catch(() => {
        localStorage.removeItem("sa_token");
        setToken(null);
        setUser(null);
        setSavedScans([]);
      });
  }, [token]);

  /* ---------- SCANNING ---------- */
  const scanWifi = async () => {
    if (isScanning) return;
    setIsScanning(true);
    setScanType("wifi");
    setStatus("Scanning Wi-Fi…");

    try {
      const res = await fetch("/api/scan/wifi");
      if (!res.ok) throw new Error("Wi-Fi request failed");
      const data = await res.json();

      setResults(data);
      setSelectedIndex(null);
      setStatus("Wi-Fi scan complete");
    } catch (e) {
      console.error(e);
      setStatus("Wi-Fi scan failed");
    } finally {
      setIsScanning(false);
    }
  };

  const scanBle = async () => {
    if (isScanning) return;
    setIsScanning(true);
    setScanType("ble");
    setStatus("Scanning Bluetooth…");

    try {
      const res = await fetch("/api/scan/ble");
      if (!res.ok) throw new Error("BLE request failed");
      const data = await res.json();

      setResults(data);
      setSelectedIndex(null);
      setStatus("Bluetooth scan complete");
    } catch (e) {
      console.error(e);
      setStatus("BLE scan failed");
    } finally {
      setIsScanning(false);
    }
  };

  const scanZigbee = async () => {
    if (isScanning) return;
    setIsScanning(true);
    setScanType("zigbee");
    setStatus("Scanning Zigbee…");

    try {
      const res = await fetch("/api/scan/zigbee");
      if (!res.ok) throw new Error("Zigbee request failed");
      const data = await res.json();

      setResults(data);
      setSelectedIndex(null);
      setStatus("Zigbee scan complete");
    } catch (e) {
      console.error(e);
      setStatus("Zigbee scan failed");
    } finally {
      setIsScanning(false);
    }
  };

  /* ---------- BEST BLUETOOTH ⭐ ---------- */
  const bestBluetooth =
    scanType === "ble" && results.length
      ? [...results].sort(
        (a, b) =>
          Number(b["Proximity (%)"] || 0) -
          Number(a["Proximity (%)"] || 0)
      )[0]
      : null;

  /* ---------- BEST ZIGBEE ⭐ ---------- */
  const bestZigbee =
    scanType === "zigbee" && results.length
      ? [...results].sort(
        (a, b) =>
          Number(b["Signal (dBm)"] || -100) -
          Number(a["Signal (dBm)"] || -100)
      )[0]
      : null;

  /* ---------- GRAPH → TABLE SYNC ---------- */
  const handlePointClick = (idx) => {
    setSelectedIndex(idx);
    const el = document.getElementById(`network-item-${idx}`);
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  };

  /* ---------- AUTH ACTIONS ---------- */
  const handleAuth = (newToken, userObj) => {
    localStorage.setItem("sa_token", newToken);
    setToken(newToken);
    setUser(userObj);
  };

  const logout = () => {
    localStorage.removeItem("sa_token");
    setToken(null);
    setUser(null);
    setSavedScans([]);
  };

  /* ---------- SAVE SCAN ---------- */
  const handleSaveScan = async () => {
    if (!token) {
      setLoginOpen(true);
      return;
    }

    if (!results.length) {
      alert("No scan data to save");
      return;
    }

    try {
      // ✅ DETECT KIND SPECIFICALLY
      const currentKind = scanType === "ble" ? "bluetooth" : scanType === "zigbee" ? "zigbee" : "wifi";

      // DEBUG: Alert what we are sending
      alert(`Saving scan as kind: ${currentKind}`);

      const payload = {
        name: `Scan ${new Date().toLocaleString()}`,
        items: results,
        kind: currentKind,
      };

      const res = await saveScan(token, payload);
      if (!res?.id) throw new Error();

      const scans = await listScans(token);
      setSavedScans(scans || []);
      alert("Scan saved successfully ✅");
    } catch (e) {
      console.error(e);
      alert("Save failed");
    }
  };

  /* ---------- DOWNLOAD ---------- */
  const handleDownloadScan = async (scanId) => {
    try {
      // Find the scan to get its details
      const scan = savedScans.find(s => s.id === scanId);
      if (!scan) return;

      const dateStr = new Date(scan.timestamp).toISOString().split('T')[0];
      const filename = `signal-analyzer - ${scan.kind} -${dateStr}.html`;

      await downloadScan(token, scanId, filename);
    } catch (e) {
      console.error(e);
      alert("Download failed");
    }
  };

  /* ---------- DELETE ---------- */
  const handleDeleteScan = async (scanId) => {
    if (!token) return;
    if (!confirm("Delete this scan permanently?")) return;

    try {
      await deleteScan(token, scanId);
      setSavedScans((prev) =>
        prev.filter((s) => s.id !== scanId)
      );
    } catch (e) {
      console.error(e);
      alert("Failed to delete scan");
    }
  };

  /* ---------- UI ---------- */
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <div className="max-w-7xl mx-auto px-6 py-8 space-y-8">

        <header className="glass-strong p-8 hover-lift">
          <div className="flex items-center justify-between">
            <div className="space-y-2">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-sky-400 to-emerald-400 flex items-center justify-center text-2xl animate-pulse">
                  📡
                </div>
                <div>
                  <h1 className="text-4xl font-bold bg-gradient-to-r from-sky-400 via-cyan-300 to-emerald-400 bg-clip-text text-transparent">
                    Signal Analyzer
                  </h1>
                  <p className="text-slate-400 text-lg">
                    Advanced wireless network scanning & signal intelligence
                  </p>
                </div>
              </div>
            </div>

            {user ? (
              <div className="flex items-center gap-4">
                <div className="text-right">
                  <div className="text-sm text-slate-400">Logged in as</div>
                  <div className="text-slate-200 font-medium">{user.email}</div>
                </div>
                <button
                  onClick={logout}
                  className="px-4 py-2 rounded-xl bg-red-500/20 hover:bg-red-500/30 border border-red-500/30 text-red-300 transition-all duration-200"
                >
                  Logout
                </button>
              </div>
            ) : (
              <button
                onClick={() => setLoginOpen(true)}
                className="btn-accent hover-glow"
              >
                🔐 Login / Sign up
              </button>
            )}
          </div>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="space-y-6">
            <ScanControl
              onWifi={scanWifi}
              onBle={scanBle}
              status={status}
              count={results.length}
              items={results}
              isScanning={isScanning}
              scanType={scanType}
              onSave={handleSaveScan}
              onZigbee={scanZigbee}
            />

            {user && (
              <SavedScansPanel
                scans={savedScans}
                onDownload={handleDownloadScan}
                onDelete={handleDeleteScan}
              />
            )}
          </div>

          <div className="lg:col-span-2 space-y-6">
            <div className="glass hover-lift hover-glow p-8">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-400 to-pink-400 flex items-center justify-center text-sm">
                  📊
                </div>
                <h2 className="text-2xl font-bold text-slate-100">
                  Live Signal Overview
                </h2>
                {scanType && (
                  <span className={`badge ${scanType === 'wifi'
                      ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                      : scanType === 'ble'
                        ? 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                        : 'bg-purple-500/20 text-purple-300 border border-purple-500/30'
                    } `}>
                    {scanType === 'wifi' ? '📶 Wi-Fi' : scanType === 'ble' ? '🔵 Bluetooth' : '🐝 Zigbee'}
                  </span>
                )}
              </div>

              {scanType === "wifi" && (
                <SignalChart
                  items={results}
                  selectedIndex={selectedIndex}
                  onPointClick={handlePointClick}
                />
              )}

              {scanType === "ble" && (
                <>
                  <BluetoothChart items={results} />
                  {bestBluetooth && (
                    <div className="mt-4 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30">
                      <div className="flex items-center gap-2 text-emerald-300 font-semibold">
                        <span className="text-xl">⭐</span>
                        <span>Best Bluetooth Device:</span>
                        <span className="text-emerald-200">{bestBluetooth["Device Name"]}</span>
                      </div>
                    </div>
                  )}
                </>
              )}

              {scanType === "zigbee" && (
                <>
                  <SignalChart
                    items={results}
                    selectedIndex={selectedIndex}
                    onPointClick={handlePointClick}
                  />
                  {bestZigbee && (
                    <div className="mt-4 p-4 rounded-xl bg-purple-500/10 border border-purple-500/30">
                      <div className="flex items-center gap-2 text-purple-300 font-semibold">
                        <span className="text-xl">⭐</span>
                        <span>Best Zigbee Device:</span>
                        <span className="text-purple-200">{bestZigbee["Name"] || "Unknown"}</span>
                      </div>
                    </div>
                  )}
                </>
              )}

              {!scanType && (
                <div className="text-center py-12 text-slate-400">
                  <div className="text-6xl mb-4 opacity-50">🔍</div>
                  <p className="text-lg">Start a scan to see live signal data</p>
                </div>
              )}
            </div>

            <div className="glass hover-lift hover-glow p-8">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-400 to-blue-400 flex items-center justify-center text-sm">
                  📋
                </div>
                <h2 className="text-2xl font-bold text-slate-100">
                  Detected Networks
                </h2>
                {results.length > 0 && (
                  <span className="badge bg-slate-600/30 text-slate-300 border border-slate-500/30">
                    {results.length} found
                  </span>
                )}
              </div>
              <NetworksTable
                items={results}
                mode={scanType}
                selectedIndex={selectedIndex}
                onSelect={setSelectedIndex}
              />
            </div>
          </div>
        </div>
      </div>

      <LoginModal
        open={loginOpen}
        onClose={() => setLoginOpen(false)}
        onAuth={handleAuth}
      />
    </div>
  );
}

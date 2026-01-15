import React from "react";
import { downloadScanHTML } from "../utils/download";

/* ---------- Status Badge ---------- */
function StatusBadge({ status }) {
  let cls = "badge bg-slate-600/30 text-slate-300 border border-slate-500/30";

  if (status.includes("Scanning"))
    cls = "badge bg-yellow-500/20 text-yellow-300 border border-yellow-500/30 animate-pulse";
  else if (status.includes("complete"))
    cls = "badge bg-emerald-500/20 text-emerald-300 border border-emerald-500/30";
  else if (status.includes("failed"))
    cls = "badge bg-red-500/20 text-red-300 border border-red-500/30";

  return <span className={cls}>{status}</span>;
}

/* ---------- Main Component ---------- */
export default function ScanControl({
  onWifi,
  onBle,
  onZigbee,
  status,
  count,
  items,
  isScanning,
  scanType,
  onSave,
}) {
  const isWifi = scanType === "wifi";
  const isBle = scanType === "ble";
  const isZigbee = scanType === "zigbee";

  return (
    <div className="glass hover-lift hover-glow p-6 space-y-6">
      {/* Header */}
      <div className="text-center">
        <div className="flex items-center justify-center gap-2 mb-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-sky-400 to-emerald-400 flex items-center justify-center text-sm">
            🔍
          </div>
          <h2 className="text-2xl font-bold tracking-tight bg-gradient-to-r from-sky-400 to-emerald-400 bg-clip-text text-transparent">
            Scanner
          </h2>
        </div>
        <p className="text-sm text-slate-400">
          Live scanning controls & signal capture
        </p>
      </div>

      {/* Buttons */}
      <div className="grid grid-cols-1 gap-4">
        {/* Wi-Fi Button */}
        <button
          onClick={onWifi}
          disabled={isScanning}
          className={`btn-scan relative group
            ${isWifi
              ? "bg-gradient-to-r from-emerald-500 via-cyan-500 to-emerald-400 text-black shadow-lg shadow-emerald-500/25"
              : "bg-emerald-500/10 text-emerald-300 hover:bg-emerald-500/20 border border-emerald-500/30"
            }
            disabled:opacity-40 disabled:cursor-not-allowed`}
        >
          <div className="flex items-center justify-center gap-3">
            <span className="text-2xl">📶</span>
            <div className="text-left">
              <div className="font-bold text-lg">Scan Wi-Fi Networks</div>
              <div className={`text-sm opacity-80 ${isWifi ? "text-black/70" : "text-emerald-300/70"
                }`}>
                Discover nearby wireless networks
              </div>
            </div>
          </div>
          {isWifi && (
            <div className="absolute inset-0 bg-white/20 rounded-xl animate-pulse"></div>
          )}
        </button>

        {/* Bluetooth Button */}
        <button
          onClick={onBle}
          disabled={isScanning}
          className={`btn-scan relative group
            ${isBle
              ? "bg-gradient-to-r from-blue-500 via-cyan-500 to-blue-400 text-black shadow-lg shadow-blue-500/25"
              : "bg-blue-500/10 text-blue-300 hover:bg-blue-500/20 border border-blue-500/30"
            }
            disabled:opacity-40 disabled:cursor-not-allowed`}
        >
          <div className="flex items-center justify-center gap-3">
            <span className="text-2xl">🔵</span>
            <div className="text-left">
              <div className="font-bold text-lg">Scan Bluetooth Devices</div>
              <div className={`text-sm opacity-80 ${isBle ? "text-black/70" : "text-blue-300/70"
                }`}>
                Find nearby Bluetooth devices
              </div>
            </div>
          </div>
          {isBle && (
            <div className="absolute inset-0 bg-white/20 rounded-xl animate-pulse"></div>
          )}
        </button>

        {/* Zigbee Button */}
        <button
          onClick={onZigbee}
          disabled={isScanning}
          className={`btn-scan relative group
            ${isZigbee
              ? "bg-gradient-to-r from-purple-500 via-pink-500 to-purple-400 text-black shadow-lg shadow-purple-500/25"
              : "bg-purple-500/10 text-purple-300 hover:bg-purple-500/20 border border-purple-500/30"
            }
            disabled:opacity-40 disabled:cursor-not-allowed`}
        >
          <div className="flex items-center justify-center gap-3">
            <span className="text-2xl">🐝</span>
            <div className="text-left">
              <div className="font-bold text-lg">Scan Zigbee Devices</div>
              <div className={`text-sm opacity-80 ${isZigbee ? "text-black/70" : "text-purple-300/70"
                }`}>
                Discover nearby Zigbee devices
              </div>
            </div>
          </div>
          {isZigbee && (
            <div className="absolute inset-0 bg-white/20 rounded-xl animate-pulse"></div>
          )}
        </button>
      </div>

      {/* Status Card */}
      <div className="glass-strong p-6 space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-slate-300">Status</span>
          <StatusBadge status={status} />
        </div>

        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-slate-300">
            {isBle ? "Devices found" : "Networks found"}
          </span>
          <div className="flex items-center gap-2">
            <span className="text-3xl font-bold bg-gradient-to-r from-sky-400 to-emerald-400 bg-clip-text text-transparent">
              {count}
            </span>
            {count > 0 && (
              <span className="text-xs text-emerald-400">✓</span>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="grid grid-cols-3 gap-3 pt-2">
          <button
            onClick={() => downloadScanHTML(items, scanType)}
            disabled={!items.length}
            className="btn-outline text-sm disabled:opacity-40 disabled:cursor-not-allowed hover-glow"
          >
            <div className="flex flex-col items-center gap-1">
              <span>⬇️</span>
              <span>Export</span>
            </div>
          </button>

          <button
            onClick={onSave}
            disabled={!items.length}
            className="btn-outline text-sm disabled:opacity-40 disabled:cursor-not-allowed hover-glow"
          >
            <div className="flex flex-col items-center gap-1">
              <span>💾</span>
              <span>Save</span>
            </div>
          </button>

          <button
            className="btn-outline text-sm hover-glow"
            onClick={() => alert("More controls coming soon")}
          >
            <div className="flex flex-col items-center gap-1">
              <span>⚙️</span>
              <span>Options</span>
            </div>
          </button>
        </div>
      </div>
    </div>
  );
}

export default function SavedScansPanel({
  scans,
  onDownload,
  onDelete,
}) {
  return (
    <div className="glass hover-lift hover-glow p-6 space-y-6">
      {/* Header */}
      <div className="text-center">
        <div className="flex items-center justify-center gap-2 mb-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-400 to-pink-400 flex items-center justify-center text-sm">
            💾
          </div>
          <h2 className="text-2xl font-bold tracking-tight bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
            Saved Scans
          </h2>
        </div>
        <p className="text-sm text-slate-400">
          Your saved network scan history
        </p>
      </div>

      {!scans.length ? (
        <div className="glass p-6 text-center">
          <div className="text-4xl mb-3 opacity-30">📁</div>
          <p className="text-slate-400">No saved scans yet</p>
        </div>
      ) : (
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {scans.map((s) => {
            // ✅ REAL saved IST time (no double conversion)
            const realISTTime = new Date(s.timestamp + "Z").toLocaleString(
              "en-IN",
              { timeZone: "Asia/Kolkata" }
            );

            return (
              <div
                key={s.id}
                className="glass-strong p-4 hover:bg-white/[0.15] transition-all duration-200"
              >
                <div className="flex items-center justify-between">
                  {/* LEFT */}
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span
                        className={`w-2 h-2 rounded-full ${s.kind === "wifi"
                            ? "bg-emerald-400"
                            : s.kind === "zigbee"
                              ? "bg-purple-400"
                              : "bg-blue-400"
                          } animate-pulse`}
                      />

                      <span className="text-sm font-semibold text-slate-200">
                        Scan
                      </span>

                      <span
                        className={`px-2 py-0.5 rounded-full text-xs font-medium whitespace-nowrap ${s.kind === "wifi"
                            ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                            : s.kind === "zigbee"
                              ? "bg-purple-500/20 text-purple-300 border border-purple-500/30"
                              : "bg-blue-500/20 text-blue-300 border border-blue-500/30"
                          }`}
                      >
                        {s.kind === "wifi" ? "📶 Wi-Fi" : s.kind === "zigbee" ? "🐝 Zigbee" : "🔵 BLE"}
                      </span>
                    </div>

                    {/* ✅ ONLY real saved time */}
                    <div className="text-xs text-slate-400 font-mono">
                      {realISTTime}
                    </div>
                  </div>

                  {/* ACTIONS */}
                  <div className="flex gap-2 ml-4">
                    <button
                      onClick={() => onDownload(s.id)}
                      className="px-3 py-1.5 text-xs rounded-lg bg-blue-500/20 hover:bg-blue-500/30 text-blue-300 border border-blue-500/30"
                    >
                      ⬇️ Download
                    </button>

                    <button
                      onClick={() => onDelete(s.id)}
                      className="px-3 py-1.5 text-xs rounded-lg bg-red-500/20 hover:bg-red-500/30 text-red-300 border border-red-500/30"
                    >
                      🗑️ Delete
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

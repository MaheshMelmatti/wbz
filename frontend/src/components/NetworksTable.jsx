export default function NetworksTable({
  items = [],
  selectedIndex,
  onSelect,
}) {
  if (!items.length) {
    return (
      <div className="glass p-8 text-center">
        <div className="text-6xl mb-4 opacity-30">🔍</div>
        <p className="text-slate-400 text-lg">No networks scanned yet</p>
        <p className="text-slate-500 text-sm mt-2">Start a scan to discover nearby networks</p>
      </div>
    );
  }

  // ⭐ Find strongest network (highest dBm)
  const strongestIndex = items.reduce((best, net, idx) => {
    const sig = net["Signal (dBm)"] ?? net.rssi ?? -100;
    const bestSig =
      items[best]["Signal (dBm)"] ?? items[best].rssi ?? -100;
    return sig > bestSig ? idx : best;
  }, 0);

  const strengthColor = (dbm) => {
    if (dbm >= -50) return "text-emerald-400";
    if (dbm >= -70) return "text-yellow-400";
    return "text-red-400";
  };

  const getSignalBars = (dbm) => {
    if (dbm >= -50) return "📶📶📶📶";
    if (dbm >= -60) return "📶📶📶";
    if (dbm >= -70) return "📶📶";
    if (dbm >= -80) return "📶";
    return "🚫";
  };

  return (
    <div className="space-y-3">
      {items.map((net, idx) => {
        const signal = net["Signal (dBm)"] ?? net.rssi ?? -90;
        const isSelected = idx === selectedIndex;
        const isStrongest = idx === strongestIndex;

        return (
          <div
            key={idx}
            id={`network-item-${idx}`}
            onClick={() => onSelect?.(idx)}
            className={`
              cursor-pointer rounded-2xl p-6 transition-all duration-300 border backdrop-blur-sm card-hover
              ${
                isSelected
                  ? "bg-sky-500/20 border-sky-400/50 shadow-lg shadow-sky-500/20 scale-[1.02]"
                  : isStrongest
                  ? "bg-emerald-500/15 border-emerald-400/40 shadow-lg shadow-emerald-500/10"
                  : "bg-white/[0.08] border-white/20 hover:bg-white/[0.12] hover:border-white/30"
              }
            `}
          >
            <div className="flex justify-between items-center">
              {/* LEFT */}
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <div className={`w-3 h-3 rounded-full ${
                    signal >= -50 ? 'bg-emerald-400 shadow-lg shadow-emerald-400/50' :
                    signal >= -70 ? 'bg-yellow-400 shadow-lg shadow-yellow-400/50' :
                    'bg-red-400 shadow-lg shadow-red-400/50'
                  } animate-pulse`}></div>
                  
                  <span className="text-xl font-bold text-slate-100">
                    {net.Name || net.ssid || "Unknown Network"}
                  </span>

                  {isStrongest && (
                    <span className="px-3 py-1 rounded-full bg-gradient-to-r from-emerald-400/20 to-cyan-400/20 text-emerald-300 font-bold text-xs border border-emerald-400/30 shadow-lg">
                      ⭐ STRONGEST
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-4 text-sm text-slate-400">
                  <span className="font-mono bg-slate-800/50 px-2 py-1 rounded border border-slate-700/50">
                    {net.BSSID || net.bssid || "—"}
                  </span>
                  <span className="px-2 py-1 rounded bg-blue-500/10 text-blue-300 border border-blue-500/30">
                    {net["Security Type"] || "Open"}
                  </span>
                  {net.Distance && (
                    <span className="px-2 py-1 rounded bg-purple-500/10 text-purple-300 border border-purple-500/30">
                      {net.Distance}
                    </span>
                  )}
                </div>
              </div>

              {/* RIGHT */}
              <div className="text-right ml-6">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-lg">{getSignalBars(signal)}</span>
                  <div
                    className={`text-2xl font-bold ${strengthColor(signal)}`}
                  >
                    {signal} dBm
                  </div>
                </div>
                
                <div className="text-xs text-slate-500">
                  {signal >= -50 ? 'Excellent' :
                   signal >= -60 ? 'Very Good' :
                   signal >= -70 ? 'Good' :
                   signal >= -80 ? 'Fair' : 'Poor'}
                </div>
              </div>
            </div>

            {/* Progress bar for signal strength */}
            <div className="mt-4 w-full bg-slate-800/50 rounded-full h-2 overflow-hidden">
              <div 
                className={`h-full rounded-full transition-all duration-500 ${
                  signal >= -50 ? 'bg-gradient-to-r from-emerald-400 to-emerald-500' :
                  signal >= -70 ? 'bg-gradient-to-r from-yellow-400 to-yellow-500' :
                  'bg-gradient-to-r from-red-400 to-red-500'
                }`}
                style={{ width: `${Math.max(0, Math.min(100, (signal + 100) * 1.25))}%` }}
              ></div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

export default function SavedScanItem({ scan, onLoad, onDownload }) {
  return (
    <div className="p-4 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 transition">
      <div className="flex justify-between items-center">
        <div>
          <div className="font-semibold text-sm">{scan.name}</div>
          <div className="text-xs text-slate-400">{scan.timestamp}</div>
          <div className="text-xs text-slate-500">
            {scan.summary}
          </div>
        </div>

        <div className="flex gap-2">
          <button
            onClick={() => onLoad(scan.id)}
            className="px-2 py-1 text-xs rounded bg-sky-500/20 hover:bg-sky-500/30"
          >
            Load
          </button>

          <button
            onClick={() => onDownload(scan.id)}
            className="px-2 py-1 text-xs rounded bg-emerald-500/20 hover:bg-emerald-500/30"
          >
            Download
          </button>
        </div>
      </div>
    </div>
  );
}

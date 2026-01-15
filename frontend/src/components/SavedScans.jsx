import React from "react";

export default function SavedScans({
  scans = [],
  onLoad,
  onDelete,
}) {
  if (!scans.length) {
    return (
      <div className="text-slate-400 text-sm">
        No saved scans yet.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {scans.map((scan) => (
        <div
          key={scan.id}
          className="flex items-center justify-between p-4 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 transition"
        >
          <div>
            <div className="font-semibold">
              {scan.name || "Unnamed Scan"}
            </div>
            <div className="text-xs text-slate-400">
              {scan.timestamp}
            </div>
            <div className="text-xs text-slate-400">
              {scan.summary}
            </div>
          </div>

          <div className="flex gap-2">
            <button
              onClick={() => onLoad(scan)}
              className="px-3 py-1 rounded bg-emerald-500/20 hover:bg-emerald-500/30 text-sm"
            >
              Load
            </button>

            <button
              onClick={() => onDelete(scan.id)}
              className="px-3 py-1 rounded bg-red-500/20 hover:bg-red-500/30 text-sm"
            >
              Delete
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}

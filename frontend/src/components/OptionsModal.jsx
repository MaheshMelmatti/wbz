export default function OptionsModal({ open, onClose }) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="w-full max-w-md rounded-xl bg-slate-900 border border-white/10 p-6 space-y-5">

        {/* Header */}
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">Scan Options</h3>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white"
          >
            ✕
          </button>
        </div>

        {/* Content (UI only) */}
        <div className="space-y-4 text-sm text-slate-300">
          <div>
            <label className="flex items-center gap-2">
              <input type="checkbox" disabled />
              Show only strong networks
            </label>
          </div>

          <div>
            <label className="flex items-center gap-2">
              <input type="radio" disabled />
              Sort by strongest signal
            </label>
          </div>

          <p className="text-xs text-slate-400">
            Advanced options will be enabled later.
          </p>
        </div>

        {/* Footer */}
        <div className="flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg bg-white/10 hover:bg-white/20 transition"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

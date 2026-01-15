import React, { useState } from "react";
import { login, signup, me } from "../services/api";

export default function LoginModal({ open, onClose, onAuth }) {
  const [mode, setMode] = useState("login"); // login | signup
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  if (!open) return null;

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError("");

    try {
      if (mode === "signup") {
        const r = await signup(email, password);
        if (r?.detail) {
          setError(r.detail);
          setBusy(false);
          return;
        }
      }

      const tokenResp = await login(email, password);
      if (tokenResp?.access_token) {
        const token = tokenResp.access_token;
        const user = await me(token);
        onAuth(token, user);
        onClose();
      } else {
        setError("Authentication failed");
      }
    } catch (err) {
      setError("Server error. Try again.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="w-full max-w-md glass-strong p-8 shadow-2xl animate-in fade-in duration-300">

        {/* Header */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-sky-400 to-emerald-400 flex items-center justify-center text-2xl">
            🔐
          </div>
          <h3 className="text-3xl font-bold bg-gradient-to-r from-sky-400 to-emerald-400 bg-clip-text text-transparent mb-2">
            {mode === "login" ? "Welcome Back" : "Join Signal Analyzer"}
          </h3>
          <p className="text-slate-400">
            {mode === "login" 
              ? "Sign in to access your saved scans" 
              : "Create an account to save your scans"}
          </p>
          
          <button
            onClick={onClose}
            className="absolute top-4 right-4 w-8 h-8 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center text-slate-400 hover:text-white transition-all duration-200"
          >
            ✕
          </button>
        </div>

        {/* Form */}
        <form onSubmit={submit} className="space-y-6">

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Email Address
            </label>
            <input
              className="w-full rounded-xl bg-black/30 border border-white/20 px-4 py-3 text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-sky-400 focus:border-transparent transition-all duration-200"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Password
            </label>
            <input
              className="w-full rounded-xl bg-black/30 border border-white/20 px-4 py-3 text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-sky-400 focus:border-transparent transition-all duration-200"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
            />
          </div>

          {error && (
            <div className="glass p-4 border border-red-500/30 bg-red-500/10">
              <div className="flex items-center gap-2 text-red-300">
                <span>⚠️</span>
                <span className="text-sm font-medium">{error}</span>
              </div>
            </div>
          )}

          {/* Submit Button */}
          <button
            type="submit"
            disabled={busy}
            className="w-full btn-accent py-4 text-lg font-bold disabled:opacity-60 disabled:cursor-not-allowed relative overflow-hidden"
          >
            {busy && (
              <div className="absolute inset-0 bg-white/20 animate-pulse"></div>
            )}
            {busy
              ? "🔄 Please wait..."
              : mode === "login"
              ? "🚀 Sign In"
              : "✨ Create Account"}
          </button>

          {/* Mode Toggle */}
          <div className="text-center pt-4 border-t border-white/10">
            <button
              type="button"
              onClick={() => {
                setMode(mode === "login" ? "signup" : "login");
                setError("");
              }}
              className="text-slate-400 hover:text-sky-400 transition-colors duration-200 font-medium"
            >
              {mode === "login"
                ? "Don't have an account? Create one →"
                : "Already have an account? Sign in →"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

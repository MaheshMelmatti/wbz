// src/services/api.js
const BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api";

/**
 * Build headers
 */
function _headers(token, contentType = "application/json") {
  const h = {};
  if (contentType) h["Content-Type"] = contentType;
  if (token) h["Authorization"] = `Bearer ${token}`;
  return h;
}

/* ---------- AUTH ---------- */

export async function signup(email, password) {
  const res = await fetch(`${BASE}/auth/signup`, {
    method: "POST",
    headers: _headers(null, "application/json"),
    body: JSON.stringify({ email, password }),
  });
  return res.json();
}

export async function login(email, password) {
  // ✅ OAuth2PasswordRequestForm → FORM URL ENCODED
  const body = new URLSearchParams();
  body.append("username", email); // MUST be "username"
  body.append("password", password);

  const res = await fetch(`${BASE}/auth/token`, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: body.toString(), // ✅ IMPORTANT FIX
  });

  return res.json();
}

export async function me(token) {
  const res = await fetch(`${BASE}/auth/me`, {
    method: "GET",
    headers: _headers(token, null), // no Content-Type needed
  });
  return res.json();
}

/* ---------- DATA ---------- */

export async function saveScan(token, payload) {
  const res = await fetch(`${BASE}/data/save`, {
    method: "POST",
    headers: _headers(token, "application/json"),
    body: JSON.stringify(payload),
  });
  return res.json();
}

export async function listScans(token) {
  const res = await fetch(`${BASE}/data/list`, {
    method: "GET",
    headers: _headers(token, null),
  });
  return res.json();
}

export async function downloadScan(token, scanId, suggestedName) {
  const res = await fetch(
    `${BASE}/${scanId}/download`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  if (!res.ok) {
    throw new Error("Download failed");
  }

  const html = await res.text();

  const blob = new Blob([html], { type: "text/html" });
  const url = window.URL.createObjectURL(blob);

  const a = document.createElement("a");
  a.href = url;
  a.download = suggestedName || `scan-${scanId}.html`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);

  window.URL.revokeObjectURL(url);
}

// DELETE a saved scan
export async function deleteScan(token, scanId) {
  const res = await fetch(
    `${BASE}/${scanId}`,
    {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );
  return res.json();
}

def security_rating(security):
    s = (security or "").upper()

    if "WPA3" in s:
        return "✅ Highly Secure"
    if "WPA2" in s:
        return "🔒 Secure"
    if "WPA" in s:
        return "⚠️ Moderate"
    if "OPEN" in s or "NONE" in s:
        return "🚫 Risky (Open)"
    if "WEP" in s:
        return "⚠️ Weak (WEP)"

    return "❓ Unknown"

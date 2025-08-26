import { useState } from "react";

export default function App() {
  const [token, setToken] = useState<string>("");
  const [email, setEmail] = useState<string>("");
  const [error, setError] = useState<string>("");

  async function handleLogin() {
    setError("");
    try {
      const res = await fetch("http://localhost:8000/oauth", {
        credentials: "include", // keep if backend sets cookies, safe to remove if not
      });
      if (!res.ok) throw new Error(`Request failed: ${res.status}`);
      const data = await res.json();
      setToken(data.token || "");
      setEmail(data.email || "");
    } catch (e: any) {
      setError(e.message || "Login failed");
    }
  }

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center p-6">
      <div className="bg-white rounded-2xl shadow-lg p-6 w-full max-w-md space-y-4">
        <h1 className="text-xl font-semibold text-gray-800">Simple OAuth Demo</h1>

        {!token ? (
          <button
            onClick={handleLogin}
            className="w-full px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700"
          >
            Log in
          </button>
        ) : (
          <div className="space-y-2 text-sm">
            <p><span className="font-medium">Email:</span> {email || "—"}</p>
            <p><span className="font-medium">Token:</span> <code>{token}</code></p>
          </div>
        )}

        {error && <p className="text-sm text-red-600">{error}</p>}
      </div>
    </div>
  );
}

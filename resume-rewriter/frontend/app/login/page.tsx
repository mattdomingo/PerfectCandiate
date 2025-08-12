"use client";
import Link from "next/link";
import { useState } from "react";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState<string | null>(null);

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setMessage("Sign-in is not enabled in this preview.");
    window.setTimeout(() => setMessage(null), 3000);
  }

  return (
    <main className="container">
      <header className="app-header" style={{marginBottom: 16}}>
        <div className="brand">
          <div className="logo" aria-hidden />
          <div>
            <div className="title">Perfect Candidate</div>
            <div className="subtitle">Login</div>
          </div>
        </div>
        <nav className="actions">
          <Link href="/app" className="btn">Use app</Link>
        </nav>
      </header>

      <div className="card" style={{maxWidth: 440, margin: "0 auto"}}>
        <h2 className="section-title" style={{marginBottom: 8}}>Welcome back</h2>
        <p className="muted" style={{marginTop: 0, marginBottom: 14}}>Sign in to continue</p>
        <form onSubmit={onSubmit} className="" aria-describedby="login-help">
          <div style={{display: "grid", gap: 10}}>
            <label>
              <div className="tiny muted" style={{marginBottom: 4}}>Email</div>
              <input className="input" type="email" required value={email} onChange={e=>setEmail(e.target.value)} placeholder="you@example.com" />
            </label>
            <label>
              <div className="tiny muted" style={{marginBottom: 4}}>Password</div>
              <input className="input" type="password" required value={password} onChange={e=>setPassword(e.target.value)} placeholder="••••••••" />
            </label>
            <button type="submit" className="btn btn-primary">Sign in</button>
            <button type="button" className="btn" aria-disabled="true" title="Not enabled">Continue with Google</button>
          </div>
          <div id="login-help" className="tiny muted" style={{marginTop: 10}}>No account needed for the demo. You can go straight to the app.</div>
        </form>
        <div style={{marginTop: 12}}>
          <span className="muted tiny">New here?</span>{" "}
          <Link href="/app" className="btn" style={{padding: "6px 10px"}}>Get started</Link>
        </div>
      </div>

      {message && (
        <output className="toast info" aria-live="polite">{message}</output>
      )}
    </main>
  );
}



import React, { useEffect, useState } from 'react';

export default function ServerControl() {
  const [status, setStatus] = useState<any>(null);
  const [logs, setLogs] = useState('');
  const [loading, setLoading] = useState(false);
  const [password, setPassword] = useState('');
  const defaultCmd = `python3 -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`;

  async function fetchStatus() {
    try {
      const r = await fetch('/admin/server/status');
      const j = await r.json();
      setStatus(j);
    } catch (e) {
      setStatus({ running: false, error: String(e) });
    }
  }

  async function fetchLogs() {
    try {
      const r = await fetch('/admin/server/logs');
      const j = await r.json();
      setLogs(j.logs || '');
    } catch (e) {
      setLogs(String(e));
    }
  }

  useEffect(() => {
    fetchStatus();
  }, []);

  async function doStart() {
    if (!password) {
      const pw = prompt('Enter admin password to start server');
      if (!pw) return;
      setPassword(pw);
    }
    setLoading(true);
    const r = await fetch('/admin/server/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password, cmd: defaultCmd.split(' ') }),
    });
    const j = await r.json();
    setLoading(false);
    await fetchStatus();
    await fetchLogs();
    alert(JSON.stringify(j));
  }

  async function doStop() {
    if (!password) {
      const pw = prompt('Enter admin password to stop server');
      if (!pw) return;
      setPassword(pw);
    }
    setLoading(true);
    const r = await fetch('/admin/server/stop', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password }),
    });
    const j = await r.json();
    setLoading(false);
    await fetchStatus();
    await fetchLogs();
    alert(JSON.stringify(j));
  }

  return (
    <div style={{ padding: 20 }}>
      <h1>Server Control</h1>
      <p>Uvicorn run command (copy):</p>
      <pre style={{ background: '#f4f4f4', padding: 10 }}>{defaultCmd}</pre>

      <div style={{ marginTop: 12 }}>
        <label>Admin password (stored in-memory for this page): </label>
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
      </div>

      <div style={{ marginTop: 12 }}>
        <button onClick={doStart} disabled={loading} style={{ marginRight: 8 }}>
          Start Server
        </button>
        <button onClick={doStop} disabled={loading} style={{ marginRight: 8 }}>
          Stop Server
        </button>
        <button onClick={() => { fetchStatus(); fetchLogs(); }} disabled={loading}>
          Refresh Status/Logs
        </button>
      </div>

      <div style={{ marginTop: 20 }}>
        <h3>Status</h3>
        <pre style={{ background: '#fff', padding: 10 }}>{JSON.stringify(status, null, 2)}</pre>
      </div>

      <div style={{ marginTop: 20 }}>
        <h3>Logs (tail)</h3>
        <div style={{ background: '#000', color: '#0f0', padding: 10, height: 300, overflow: 'auto', whiteSpace: 'pre-wrap' }}>{logs}</div>
      </div>

    </div>
  );
}

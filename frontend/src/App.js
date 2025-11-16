import React, { useState, useEffect } from 'react';
import './App.css';

const API_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

function App() {
  const [status, setStatus] = useState('loading');

  useEffect(() => {
    // Check backend health
    fetch(`${API_URL}/api/health`)
      .then(res => res.json())
      .then(data => {
        setStatus('connected');
      })
      .catch(err => {
        setStatus('error');
        console.error('Backend connection error:', err);
      });
  }, []);

  return (
    <div className="App">
      <header className="App-header">
        <h1>Quantum Sprout</h1>
        <p>Jira Productivity Analytics</p>
        <p>Status: {status}</p>
        <p>Backend: {API_URL}</p>
      </header>
    </div>
  );
}

export default App;


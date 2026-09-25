import os
F = r'D:\PROJECTS\trademind\frontend\src'
def w(p, c):
    fp = os.path.join(F, p)
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    with open(fp, 'w', encoding='utf-8') as f: f.write(c)
    print(f'  {p}')

# App.tsx
w('App.tsx', """import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useState } from 'react';
import MainLayout from './layouts/MainLayout';
import OverviewPage from './pages/OverviewPage';
import SignalsPage from './pages/SignalsPage';
import ModelLabPage from './pages/ModelLabPage';
import BacktestPage from './pages/BacktestPage';
import DataPage from './pages/DataPage';

export default function App() {
  const [symbol, setSymbol] = useState('^NSEI');
  return (
    <BrowserRouter>
      <MainLayout symbol={symbol} onSymbolChange={setSymbol}>
        <Routes>
          <Route path="/" element={<Navigate to="/overview" replace />} />
          <Route path="/overview" element={<OverviewPage symbol={symbol} />} />
          <Route path="/signals" element={<SignalsPage symbol={symbol} />} />
          <Route path="/model-lab" element={<ModelLabPage symbol={symbol} />} />
          <Route path="/backtest" element={<BacktestPage symbol={symbol} />} />
          <Route path="/data" element={<DataPage symbol={symbol} />} />
        </Routes>
      </MainLayout>
    </BrowserRouter>
  );
}
""")

# main.tsx
w('main.tsx', """import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode><App /></React.StrictMode>
)
""")

# MainLayout
w('layouts/MainLayout.tsx', """import { ReactNode, useEffect, useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { LayoutDashboard, Signal, FlaskConical, LineChart, Database, AlertTriangle } from 'lucide-react';
import { api } from '../services/api';

const NAV = [
  { to: '/overview', label: 'Overview', icon: LayoutDashboard },
  { to: '/signals', label: 'Signals', icon: Signal },
  { to: '/model-lab', label: 'Model Lab', icon: FlaskConical },
  { to: '/backtest', label: 'Backtest', icon: LineChart },
  { to: '/data', label: 'Data', icon: Database },
];

const ASSETS = [
  { symbol: '^NSEI', name: 'NIFTY 50' },
  { symbol: 'SPY', name: 'S&P 500 ETF' },
  { symbol: 'QQQ', name: 'Nasdaq 100' },
  { symbol: '^GSPC', name: 'S&P 500 Index' },
];

interface Props { symbol: string; onSymbolChange: (s: string) => void; children: ReactNode; }

export default function MainLayout({ symbol, onSymbolChange, children }: Props) {
  const location = useLocation();
  const [regime, setRegime] = useState<any>(null);
  const pageName = NAV.find(n => n.to === location.pathname)?.label || 'Overview';
  const assetName = ASSETS.find(a => a.symbol === symbol)?.name || symbol;

  useEffect(() => {
    api.getRegime(symbol).then(setRegime).catch(() => setRegime(null));
  }, [symbol]);

  const regimeLabel = regime?.regime || '';
  const regimeColor = regimeLabel === 'BULL' ? 'text-buy' : regimeLabel === 'BEAR' ? 'text-sell' : 'text-text-muted';

  return (
    <div className="flex h-screen overflow-hidden bg-bg-primary">
      {/* Sidebar */}
      <aside className="w-56 border-r border-border flex flex-col bg-bg-card">
        <div className="p-4 border-b border-border">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-accent/20 flex items-center justify-center text-accent font-bold text-sm">T</div>
            <div>
              <h1 className="text-sm font-bold text-text-primary tracking-wide">TradeMind</h1>
              <p className="text-[10px] text-text-muted uppercase tracking-[0.2em] font-mono">Research Console</p>
            </div>
          </div>
        </div>
        <nav className="flex-1 p-3 space-y-1">
          <p className="text-[10px] uppercase tracking-wider text-text-muted mb-2 px-2 font-mono">Workspace</p>
          {NAV.map(({ to, label, icon: Icon }) => (
            <NavLink key={to} to={to}
              className={({ isActive }) =>
                `flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-all ${
                  isActive ? 'bg-accent/15 text-accent font-medium' : 'text-text-secondary hover:bg-bg-card-hover hover:text-text-primary'
                }`
              }>
              {({ isActive }) => (<>
                {isActive && <span className="w-1.5 h-1.5 rounded-full bg-accent" />}
                <Icon size={16} />
                <span>{label}</span>
              </>)}
            </NavLink>
          ))}
        </nav>
        <div className="p-3 m-3 rounded-lg border border-accent/30 bg-accent/5">
          <p className="text-[10px] uppercase tracking-wider text-accent font-mono font-bold">Research Mode</p>
          <p className="text-[10px] text-text-muted mt-1">Historical simulation. No live execution or financial advice.</p>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="h-12 border-b border-border bg-bg-card/50 flex items-center justify-between px-5">
          <div className="flex items-center gap-2 text-xs text-text-muted font-mono uppercase tracking-wider">
            <span className="text-text-primary font-medium">{pageName}</span>
            <span className="text-text-muted">·</span>
            <span>{new Date().toISOString().slice(0, 10)}</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <span className="text-[10px] text-text-muted uppercase font-mono">Asset</span>
              <select value={symbol} onChange={e => onSymbolChange(e.target.value)}
                className="bg-bg-card border border-border rounded-md px-2.5 py-1 text-sm text-text-primary font-medium cursor-pointer focus:outline-none focus:border-accent">
                {ASSETS.map(a => <option key={a.symbol} value={a.symbol}>{a.name}</option>)}
              </select>
            </div>
            {regimeLabel && (
              <div className={`border border-border rounded-md px-2.5 py-1 text-xs font-mono ${regimeColor}`}>
                Regime <span className="font-bold">{regimeLabel}</span>
                {regime?.score ? ` · ${(regime.score * 100).toFixed(0)}%` : ''}
              </div>
            )}
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto p-5">
          {children}
        </main>

        {/* Footer */}
        <footer className="h-8 border-t border-border bg-bg-card/30 flex items-center justify-between px-5 text-[10px] text-text-muted font-mono">
          <div className="flex items-center gap-1">
            <AlertTriangle size={10} />
            <span>DISCLAIMER — TradeMind is a university AML mini-project. All figures are historical. No financial advice.</span>
          </div>
          <div className="flex items-center gap-4">
            <span>Dataset: Public Historical</span>
            <span>Pipeline: Features → Regimes → Models → Backtest</span>
          </div>
        </footer>
      </div>
    </div>
  );
}
""")

print('App & Layout done')
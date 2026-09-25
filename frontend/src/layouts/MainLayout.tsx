import type { ReactNode } from 'react';
import { useEffect, useState } from 'react';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import { Globe, Search, Filter, ArrowRightLeft } from 'lucide-react';
import { api } from '../services/api';

const NAV = [
  { to: '/market', label: 'Market Overview', icon: Globe },
  { to: '/screener', label: 'Screener', icon: Filter },
  { to: '/compare', label: 'Compare', icon: ArrowRightLeft },
];

interface Props { symbol: string; onSymbolChange: (s: string) => void; children: ReactNode; }

export default function MainLayout({ symbol, onSymbolChange, children }: Props) {
  const location = useLocation();
  const navigate = useNavigate();
  const [regime, setRegime] = useState<any>(null);
  const pageName = NAV.find(n => n.to === location.pathname)?.label || 'Stock Analyzer';

  // Only fetch regime if on a stock analyzer page and symbol is set
  useEffect(() => {
    if (location.pathname.startsWith('/stock/')) {
        api.getRegime(symbol).then(setRegime).catch(() => setRegime(null));
    } else {
        setRegime(null);
    }
  }, [symbol, location.pathname]);

  const regimeLabel = regime?.regime || '';
  const regimeColor = regimeLabel === 'BULL' ? 'text-buy' : regimeLabel === 'BEAR' ? 'text-sell' : 'text-text-muted';

  return (
    <div className="flex h-screen overflow-hidden bg-bg-primary">
      {/* Sidebar */}
      <aside className="w-56 border-r border-border flex flex-col bg-bg-card">
        <div className="p-4 border-b border-border cursor-pointer" onClick={() => navigate('/market')}>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-accent/20 flex items-center justify-center text-accent font-bold text-sm">T2</div>
            <div>
              <h1 className="text-sm font-bold text-text-primary tracking-wide">TradeMind 2.0</h1>
              <p className="text-[10px] text-text-muted uppercase tracking-[0.2em] font-mono">Platform</p>
            </div>
          </div>
        </div>
        
        {/* Navigation */}
        <nav className="flex-1 p-3 space-y-1">
          <p className="text-[10px] uppercase tracking-wider text-text-muted mb-2 px-2 font-mono">Platform Tools</p>
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
          
          <div className="pt-4 mt-4 border-t border-border/50">
             <p className="text-[10px] uppercase tracking-wider text-text-muted mb-2 px-2 font-mono">Current Asset</p>
             <NavLink to={`/stock/${symbol}`}
              className={({ isActive }) =>
                `flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-all ${
                  isActive ? 'bg-accent/15 text-accent font-medium' : 'text-text-secondary hover:bg-bg-card-hover hover:text-text-primary'
                }`
              }>
              <Search size={16} />
              <span className="truncate">{symbol} Analyzer</span>
             </NavLink>
          </div>
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
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <form onSubmit={(e) => {
                e.preventDefault();
                const fd = new FormData(e.currentTarget);
                const query = fd.get('symbol')?.toString().toUpperCase().trim();
                if (query) {
                  onSymbolChange(query);
                  navigate(`/stock/${query}`);
                }
              }} className="relative">
                <input 
                  name="symbol"
                  type="text" 
                  placeholder="Search ticker (e.g. RELIANCE.NS)"
                  className="bg-bg-card border border-border rounded-md px-3 py-1.5 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent w-56 uppercase"
                />
                <button type="submit" className="absolute right-2 top-1/2 -translate-y-1/2 text-text-muted hover:text-accent">
                  <Search size={14} />
                </button>
              </form>
            </div>
            {regimeLabel && (
              <div className={`border border-border rounded-md px-2.5 py-1.5 text-xs font-mono flex items-center gap-1.5 ${regimeColor}`}>
                <div className={`w-2 h-2 rounded-full ${regimeLabel === 'BULL' ? 'bg-buy' : regimeLabel === 'BEAR' ? 'bg-sell' : 'bg-text-muted'}`} />
                <span>Regime: <span className="font-bold">{regimeLabel}</span></span>
              </div>
            )}
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto p-5 relative">
          {children}
        </main>
      </div>
    </div>
  );
}

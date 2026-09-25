import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { LineChart, Line, XAxis, YAxis, Tooltip as RechartsTooltip, ResponsiveContainer } from 'recharts';
import { Loader2, ArrowRight } from 'lucide-react';

export default function MarketOverviewPage() {
  const navigate = useNavigate();
  const [assets, setAssets] = useState<any[]>([]);
  const [niftyPrices, setNiftyPrices] = useState<any[]>([]);
  const [niftyRegime, setNiftyRegime] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.getAssets().catch(() => ({ assets: [] })),
      api.getPrices('^NSEI', 100).catch(() => ({ prices: [] })),
      api.getRegime('^NSEI').catch(() => null)
    ]).then(([a, p, r]) => {
      setAssets(a.assets || []);
      setNiftyPrices(p.prices || []);
      setNiftyRegime(r);
      setLoading(false);
    });
  }, []);

  if (loading) return (
    <div className="flex flex-col items-center justify-center h-96 gap-4">
      <Loader2 className="animate-spin text-accent" size={32} />
      <span className="text-text-primary font-medium">Loading Market Overview...</span>
    </div>
  );

  const regimeLabel = niftyRegime?.regime || 'UNKNOWN';
  const regimeColor = regimeLabel === 'BULL' ? 'text-buy' : regimeLabel === 'BEAR' ? 'text-sell' : 'text-text-muted';

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-end">
        <div>
           <h1 className="text-2xl font-bold text-text-primary">Market Overview</h1>
           <p className="text-sm text-text-muted font-mono">Global Market State & Supported Universe</p>
        </div>
      </div>

      <div className="grid grid-cols-12 gap-4">
        {/* NIFTY 50 Overview */}
        <div className="col-span-12 lg:col-span-8 bg-bg-card border border-border rounded-lg p-4">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-[10px] uppercase tracking-wider text-text-muted font-mono">Benchmark: NIFTY 50 (^NSEI)</h2>
            {niftyRegime && (
              <div className={`border border-border rounded-md px-2.5 py-1.5 text-xs font-mono flex items-center gap-1.5 ${regimeColor}`}>
                <div className={`w-2 h-2 rounded-full ${regimeLabel === 'BULL' ? 'bg-buy' : regimeLabel === 'BEAR' ? 'bg-sell' : 'bg-text-muted'}`} />
                <span>Market Regime: <span className="font-bold">{regimeLabel}</span></span>
              </div>
            )}
          </div>
          
          {niftyPrices.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={niftyPrices}>
                <XAxis dataKey="date" tick={{ fontSize: 9, fill: '#64748b' }} tickFormatter={(v) => v.slice(5, 10)} />
                <YAxis domain={['auto', 'auto']} tick={{ fontSize: 9, fill: '#64748b' }} />
                <RechartsTooltip contentStyle={{ background: '#0d1b2a', border: '1px solid #1e3a5f', borderRadius: 8, fontSize: 11 }} />
                <Line type="monotone" dataKey="close" stroke="#14b8a6" strokeWidth={2} dot={false} name="NIFTY 50" />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[250px] flex items-center justify-center text-text-muted">No benchmark data.</div>
          )}
        </div>
        
        {/* Summary Stats */}
        <div className="col-span-12 lg:col-span-4 bg-bg-card border border-border rounded-lg p-4 flex flex-col">
            <h2 className="text-[10px] uppercase tracking-wider text-text-muted font-mono mb-4">Platform Stats</h2>
            <div className="flex-1 space-y-4">
               <div className="bg-bg-primary rounded-lg p-4 border border-border">
                  <p className="text-3xl font-bold font-mono text-accent">{assets.length}</p>
                  <p className="text-sm text-text-muted">Supported Equities</p>
               </div>
               <div className="bg-bg-primary rounded-lg p-4 border border-border">
                  <p className="text-xl font-bold font-mono text-text-primary">TradeMind Global</p>
                  <p className="text-sm text-text-muted">Active Model Engine</p>
               </div>
               <div className="bg-bg-primary rounded-lg p-4 border border-border">
                  <p className="text-xl font-bold font-mono text-text-primary">Rule-Based / K-Means</p>
                  <p className="text-sm text-text-muted">Regime Detector</p>
               </div>
            </div>
        </div>
      </div>

      {/* Universe Table */}
      <div className="bg-bg-card border border-border rounded-lg p-4">
        <h2 className="text-[10px] uppercase tracking-wider text-text-muted font-mono mb-4">Supported Security Universe</h2>
        
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {assets.map((asset) => (
             <div 
               key={asset.symbol} 
               onClick={() => navigate(`/stock/${asset.symbol}`)}
               className="group flex flex-col p-3 rounded-lg border border-border hover:border-accent/50 hover:bg-accent/5 cursor-pointer transition-colors"
             >
                <div className="flex justify-between items-center">
                    <span className="font-bold text-text-primary">{asset.symbol.replace('.NS', '')}</span>
                    <ArrowRight size={14} className="text-text-muted group-hover:text-accent transition-colors" />
                </div>
                <span className="text-xs text-text-muted truncate mt-1">{asset.name}</span>
             </div>
          ))}
        </div>
      </div>
    </div>
  );
}

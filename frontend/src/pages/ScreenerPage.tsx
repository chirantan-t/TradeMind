import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { Loader2, ArrowRight } from 'lucide-react';

function SignalBadge({ signal }: { signal: string }) {
  const colors: Record<string, string> = {
    BUY: 'text-buy bg-buy/10 border-buy/30',
    HOLD: 'text-hold bg-hold/10 border-hold/30',
    SELL: 'text-sell bg-sell/10 border-sell/30',
  };
  const cls = colors[signal] || colors.HOLD;
  return <span className={`inline-block border rounded-md px-2 py-0.5 font-mono font-bold text-xs ${cls}`}>{signal}</span>;
}

export default function ScreenerPage() {
  const navigate = useNavigate();
  const [screenerData, setScreenerData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // We'll run the screener for a subset of prominent stocks for performance 
  // since the backend doesn't have a bulk screener endpoint yet.
  const SCREENER_UNIVERSE = ['RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS'];

  useEffect(() => {
    const fetchScreener = async () => {
      try {
        const promises = SCREENER_UNIVERSE.map(sym => api.getPrediction(sym).catch(() => null));
        const results = await Promise.all(promises);
        
        const valid = results.filter(r => r !== null);
        setScreenerData(valid);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    
    fetchScreener();
  }, []);

  if (loading) return (
    <div className="flex flex-col items-center justify-center h-96 gap-4">
      <Loader2 className="animate-spin text-accent" size={32} />
      <span className="text-text-primary font-medium">Running global AI screener...</span>
    </div>
  );

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-end">
        <div>
           <h1 className="text-2xl font-bold text-text-primary">AI Screener</h1>
           <p className="text-sm text-text-muted font-mono">Filter and discover opportunities across the universe</p>
        </div>
      </div>

      <div className="bg-bg-card border border-border rounded-lg p-4">
        <h2 className="text-[10px] uppercase tracking-wider text-text-muted font-mono mb-4">Screener Results</h2>
        
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-text-muted font-mono uppercase tracking-wider border-b border-border/50 text-left">
                <th className="pb-3 font-medium">Symbol</th>
                <th className="pb-3 font-medium text-center">AI Signal</th>
                <th className="pb-3 font-medium text-right">Confidence</th>
                <th className="pb-3 font-medium text-right">Regime</th>
                <th className="pb-3 font-medium text-right">Top Driver</th>
                <th className="pb-3 font-medium text-right">Action</th>
              </tr>
            </thead>
            <tbody>
              {screenerData.map((data) => {
                  const rLabel = data.regime?.label || 'UNKNOWN';
                  const rColor = rLabel === 'BULL' ? 'text-buy' : rLabel === 'BEAR' ? 'text-sell' : 'text-text-muted';
                  const topDriver = data.feature_drivers?.[0];
                  
                  return (
                    <tr key={data.symbol} className="border-b border-border/20 hover:bg-bg-card-hover transition-colors">
                      <td className="py-4 font-bold text-text-primary">{data.symbol.replace('.NS', '')}</td>
                      <td className="py-4 text-center"><SignalBadge signal={data.signal} /></td>
                      <td className="py-4 text-right font-mono text-text-secondary">{data.confidence.toFixed(2)}</td>
                      <td className={`py-4 text-right font-mono font-bold ${rColor}`}>{rLabel}</td>
                      <td className="py-4 text-right text-text-secondary text-xs truncate max-w-[120px]">
                          {topDriver ? topDriver.feature : 'N/A'}
                      </td>
                      <td className="py-4 text-right">
                          <button 
                            onClick={() => navigate(`/stock/${data.symbol}`)}
                            className="inline-flex items-center gap-1 text-xs text-accent hover:text-accent-dim"
                          >
                            Analyze <ArrowRight size={12} />
                          </button>
                      </td>
                    </tr>
                  )
              })}
              
              {screenerData.length === 0 && (
                  <tr>
                      <td colSpan={6} className="py-8 text-center text-text-muted">
                          No screener data available. Make sure the global model is trained.
                      </td>
                  </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

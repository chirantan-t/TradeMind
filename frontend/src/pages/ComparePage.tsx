import { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Loader2, ArrowRightLeft } from 'lucide-react';

function SignalBadge({ signal }: { signal: string }) {
  const colors: Record<string, string> = {
    BUY: 'text-buy bg-buy/10 border-buy/30',
    HOLD: 'text-hold bg-hold/10 border-hold/30',
    SELL: 'text-sell bg-sell/10 border-sell/30',
  };
  const cls = colors[signal] || colors.HOLD;
  return <span className={`inline-block border rounded-md px-2 py-0.5 font-mono font-bold text-lg ${cls}`}>{signal}</span>;
}

export default function ComparePage() {
  const [sym1, setSym1] = useState('RELIANCE.NS');
  const [sym2, setSym2] = useState('TCS.NS');
  
  const [data1, setData1] = useState<any>(null);
  const [data2, setData2] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchComparison = async () => {
    if (!sym1 || !sym2) return;
    setLoading(true);
    setError('');
    
    try {
        const [p1, f1, b1, p2, f2, b2] = await Promise.all([
            api.getPrediction(sym1).catch(() => null),
            api.getFundamentals(sym1).catch(() => null),
            api.getBacktest(sym1).catch(() => null),
            api.getPrediction(sym2).catch(() => null),
            api.getFundamentals(sym2).catch(() => null),
            api.getBacktest(sym2).catch(() => null),
        ]);
        
        setData1({ pred: p1, fund: f1?.fundamentals, bt: b1?.metrics });
        setData2({ pred: p2, fund: f2?.fundamentals, bt: b2?.metrics });
        
        if (!p1 && !p2) {
            setError('Could not fetch data for these symbols. Ensure the global model is trained for them.');
        }
    } catch (e) {
        setError('Comparison failed.');
    } finally {
        setLoading(false);
    }
  };

  useEffect(() => {
    fetchComparison();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-end">
        <div>
           <h1 className="text-2xl font-bold text-text-primary">Compare Assets</h1>
           <p className="text-sm text-text-muted font-mono">Side-by-side AI and fundamental analysis</p>
        </div>
      </div>

      <div className="bg-bg-card border border-border rounded-lg p-4 flex gap-4 items-center">
         <input 
            value={sym1}
            onChange={(e) => setSym1(e.target.value.toUpperCase())}
            placeholder="Symbol 1"
            className="bg-bg-primary border border-border rounded-md px-3 py-2 text-sm focus:border-accent outline-none"
         />
         <div className="text-text-muted"><ArrowRightLeft size={20} /></div>
         <input 
            value={sym2}
            onChange={(e) => setSym2(e.target.value.toUpperCase())}
            placeholder="Symbol 2"
            className="bg-bg-primary border border-border rounded-md px-3 py-2 text-sm focus:border-accent outline-none"
         />
         <button 
           onClick={fetchComparison}
           className="bg-accent hover:bg-accent-dim text-bg-primary font-medium px-4 py-2 rounded-md transition-colors"
         >
             Compare
         </button>
      </div>

      {loading ? (
          <div className="flex flex-col items-center justify-center h-64 gap-4">
              <Loader2 className="animate-spin text-accent" size={32} />
              <span className="text-text-primary font-medium">Generating comparison...</span>
          </div>
      ) : error ? (
          <div className="p-4 bg-sell/10 text-sell border border-sell/30 rounded-lg">{error}</div>
      ) : data1 && data2 ? (
          <div className="grid grid-cols-2 gap-6">
              {/* Asset 1 */}
              <div className="space-y-4">
                  <h2 className="text-xl font-bold text-center border-b border-border pb-2">{sym1}</h2>
                  
                  <div className="bg-bg-card border border-border rounded-lg p-4 text-center">
                      <p className="text-[10px] uppercase tracking-wider text-text-muted font-mono mb-2">Global AI Signal</p>
                      {data1.pred ? <SignalBadge signal={data1.pred.signal} /> : <span className="text-text-muted">N/A</span>}
                      {data1.pred && <p className="text-xs text-text-muted mt-2">Confidence: {data1.pred.confidence.toFixed(2)}</p>}
                  </div>
                  
                  <div className="bg-bg-card border border-border rounded-lg p-4">
                      <p className="text-[10px] uppercase tracking-wider text-text-muted font-mono mb-3">Fundamentals</p>
                      <div className="space-y-2">
                         <div className="flex justify-between text-sm"><span className="text-text-muted">P/E Ratio</span><span className="font-mono">{data1.fund?.pe_ratio?.toFixed(2) || '—'}</span></div>
                         <div className="flex justify-between text-sm"><span className="text-text-muted">ROE</span><span className="font-mono">{data1.fund?.roe ? (data1.fund.roe*100).toFixed(1)+'%' : '—'}</span></div>
                         <div className="flex justify-between text-sm"><span className="text-text-muted">Debt/Eq</span><span className="font-mono">{data1.fund?.debt_to_equity?.toFixed(2) || '—'}</span></div>
                      </div>
                  </div>
                  
                  <div className="bg-bg-card border border-border rounded-lg p-4">
                      <p className="text-[10px] uppercase tracking-wider text-text-muted font-mono mb-3">Performance (2Yr Backtest)</p>
                      <div className="space-y-2">
                         <div className="flex justify-between text-sm"><span className="text-text-muted">Sharpe</span><span className="font-mono">{data1.bt?.sharpe_ratio?.toFixed(2) || '—'}</span></div>
                         <div className="flex justify-between text-sm"><span className="text-text-muted">Win Rate</span><span className="font-mono">{data1.bt?.win_rate ? (data1.bt.win_rate*100).toFixed(0)+'%' : '—'}</span></div>
                         <div className="flex justify-between text-sm"><span className="text-text-muted">Max DD</span><span className="font-mono text-sell">{data1.bt?.max_drawdown ? (data1.bt.max_drawdown*100).toFixed(1)+'%' : '—'}</span></div>
                      </div>
                  </div>
              </div>
              
              {/* Asset 2 */}
              <div className="space-y-4">
                  <h2 className="text-xl font-bold text-center border-b border-border pb-2">{sym2}</h2>
                  
                  <div className="bg-bg-card border border-border rounded-lg p-4 text-center">
                      <p className="text-[10px] uppercase tracking-wider text-text-muted font-mono mb-2">Global AI Signal</p>
                      {data2.pred ? <SignalBadge signal={data2.pred.signal} /> : <span className="text-text-muted">N/A</span>}
                      {data2.pred && <p className="text-xs text-text-muted mt-2">Confidence: {data2.pred.confidence.toFixed(2)}</p>}
                  </div>
                  
                  <div className="bg-bg-card border border-border rounded-lg p-4">
                      <p className="text-[10px] uppercase tracking-wider text-text-muted font-mono mb-3">Fundamentals</p>
                      <div className="space-y-2">
                         <div className="flex justify-between text-sm"><span className="text-text-muted">P/E Ratio</span><span className="font-mono">{data2.fund?.pe_ratio?.toFixed(2) || '—'}</span></div>
                         <div className="flex justify-between text-sm"><span className="text-text-muted">ROE</span><span className="font-mono">{data2.fund?.roe ? (data2.fund.roe*100).toFixed(1)+'%' : '—'}</span></div>
                         <div className="flex justify-between text-sm"><span className="text-text-muted">Debt/Eq</span><span className="font-mono">{data2.fund?.debt_to_equity?.toFixed(2) || '—'}</span></div>
                      </div>
                  </div>
                  
                  <div className="bg-bg-card border border-border rounded-lg p-4">
                      <p className="text-[10px] uppercase tracking-wider text-text-muted font-mono mb-3">Performance (2Yr Backtest)</p>
                      <div className="space-y-2">
                         <div className="flex justify-between text-sm"><span className="text-text-muted">Sharpe</span><span className="font-mono">{data2.bt?.sharpe_ratio?.toFixed(2) || '—'}</span></div>
                         <div className="flex justify-between text-sm"><span className="text-text-muted">Win Rate</span><span className="font-mono">{data2.bt?.win_rate ? (data2.bt.win_rate*100).toFixed(0)+'%' : '—'}</span></div>
                         <div className="flex justify-between text-sm"><span className="text-text-muted">Max DD</span><span className="font-mono text-sell">{data2.bt?.max_drawdown ? (data2.bt.max_drawdown*100).toFixed(1)+'%' : '—'}</span></div>
                      </div>
                  </div>
              </div>
          </div>
      ) : null}
    </div>
  );
}

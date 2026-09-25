import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { api } from '../services/api';
import { LineChart, Line, XAxis, YAxis, Tooltip as RechartsTooltip, ResponsiveContainer } from 'recharts';
import { Loader2, AlertCircle } from 'lucide-react';
import { Tooltip } from '../components/Tooltip';

function MetricCard({ label, value, color, tooltip }: { label: string; value: string; color?: string, tooltip?: string }) {
  return (
    <div className="bg-bg-card border border-border rounded-lg p-3">
      <div className="flex items-center gap-1 mb-1">
        <p className="text-[10px] uppercase tracking-wider text-text-muted font-mono">{label}</p>
        {tooltip && (
          <Tooltip text={tooltip}>
            <div className="w-3 h-3" />
          </Tooltip>
        )}
      </div>
      <p className={`text-lg font-bold font-mono ${color || 'text-text-primary'}`}>{value}</p>
    </div>
  );
}

function SignalBadge({ signal, size = 'lg' }: { signal: string; size?: string }) {
  const colors: Record<string, string> = {
    BUY: 'text-buy bg-buy/10 border-buy/30',
    HOLD: 'text-hold bg-hold/10 border-hold/30',
    SELL: 'text-sell bg-sell/10 border-sell/30',
  };
  const cls = colors[signal] || colors.HOLD;
  return <span className={`inline-block border rounded-md px-2 py-0.5 font-mono font-bold ${size === 'lg' ? 'text-3xl px-4 py-1' : 'text-xs'} ${cls}`}>{signal}</span>;
}

function ProbBar({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="mb-2">
      <div className="flex justify-between text-xs mb-0.5">
        <span className={color}>{label}</span>
        <span className="text-text-secondary font-mono">{value.toFixed(2)}</span>
      </div>
      <div className="h-1.5 bg-bg-primary rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color.replace('text-', 'bg-')}`} style={{ width: `${value * 100}%` }} />
      </div>
    </div>
  );
}

function DriverBar({ feature, value }: { feature: string; value: number }) {
  const isPos = value >= 0;
  const w = Math.min(Math.abs(value) * 500, 100);
  const humanize = (n: string) => {
    const m: Record<string, string> = { rsi_14: 'RSI(14)', macd: 'MACD', volatility_20d: 'Realized vol',
      momentum_14: '14d momentum', return_14d: '14d return', volume_zscore: 'Vol z-score',
      trend_slope_20: 'Trend slope', atr_pct: 'ATR%', price_sma_50_ratio: 'Price/SMA50' };
    return m[n] || n.replace(/_/g, ' ');
  };
  return (
    <div className="flex items-center justify-between mb-2">
      <span className="text-xs text-text-primary w-28 truncate">{humanize(feature)}</span>
      <div className="flex-1 mx-2"><div className="h-1.5 rounded-full overflow-hidden bg-bg-primary">
        <div className={`h-full rounded-full ${isPos ? 'bg-accent' : 'bg-sell'}`} style={{ width: `${w}%` }} /></div></div>
      <span className={`text-xs font-mono w-12 text-right ${isPos ? 'text-accent' : 'text-sell'}`}>{value > 0 ? '+' : ''}{value.toFixed(2)}</span>
    </div>
  );
}

export default function StockAnalyzerPage({ onSymbolChange }: { onSymbolChange: (s: string) => void }) {
  const { symbol } = useParams();
  
  const [pred, setPred] = useState<any>(null);
  const [bt, setBt] = useState<any>(null);
  const [eq, setEq] = useState<any>(null);
  const [funds, setFunds] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (symbol) {
        onSymbolChange(symbol);
        fetchData();
    }
  }, [symbol, onSymbolChange]);

  const fetchData = () => {
    if (!symbol) return;
    setLoading(true);
    setError('');
    Promise.all([
      api.getPrediction(symbol).catch(() => null),
      api.getBacktest(symbol).catch(() => null),
      api.getEquity(symbol).catch(() => null),
      api.getFundamentals(symbol).catch(() => null),
    ]).then(([p, b, e, f]) => {
      if (!p && !b) {
        setError('No data found for this stock. Make sure the global model is trained and this stock is in the universe.');
      } else {
        setPred(p); setBt(b); setEq(e); setFunds(f?.fundamentals || {});
      }
      setLoading(false);
    });
  };

  if (loading) return (
    <div className="flex flex-col items-center justify-center h-96 gap-4">
      <Loader2 className="animate-spin text-accent" size={32} />
      <span className="text-text-primary font-medium">Analyzing stock data...</span>
    </div>
  );

  if (error) return (
    <div className="flex flex-col items-center justify-center h-96 gap-4">
      <div className="w-16 h-16 rounded-2xl bg-sell/10 flex items-center justify-center"><AlertCircle className="text-sell" size={32} /></div>
      <h2 className="text-xl font-bold">Analysis Failed</h2>
      <p className="text-text-muted text-sm max-w-md text-center">{error}</p>
    </div>
  );

  const p = pred || {};
  const probs = p.probabilities || {};
  const regime = p.regime || {};
  const btm = bt?.metrics || {};
  const eqData = eq?.equity_curve || [];
  const drivers = (p.feature_drivers || []).slice(0, 4);

  // Format equity for chart (sample every nth point for performance)
  const step = Math.max(1, Math.floor(eqData.length / 200));
  const chartData = eqData.filter((_: any, i: number) => i % step === 0 || i === eqData.length - 1);

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-end mb-2">
        <div>
           <h1 className="text-2xl font-bold text-text-primary">{symbol}</h1>
           <p className="text-sm text-text-muted font-mono">Market Regiment & Predictability Analysis</p>
        </div>
      </div>

      {/* Row 1: Signal + Fundamentals + Probabilities */}
      <div className="grid grid-cols-12 gap-4">
        <div className="col-span-5 bg-bg-card border border-border rounded-lg p-4">
          <div className="flex justify-between items-start mb-3">
            <p className="text-[10px] uppercase tracking-wider text-text-muted font-mono">(A) Global AI Signal</p>
            <p className="text-[10px] text-text-muted font-mono">model · {p.model || '—'}</p>
          </div>
          <div className="flex items-center gap-4 mb-3">
            <SignalBadge signal={p.signal || 'HOLD'} />
            <span className="text-xs bg-bg-primary border border-border rounded px-2 py-1 font-mono text-text-secondary">
              confidence {(p.confidence || 0).toFixed(2)}
            </span>
          </div>
          <p className="text-sm text-text-secondary leading-relaxed">{p.explanation || 'No explanation available.'}</p>
        </div>

        <div className="col-span-3 bg-bg-card border border-border rounded-lg p-4">
          <p className="text-[10px] uppercase tracking-wider text-text-muted font-mono mb-3">(B) Fundamentals</p>
          <div className="space-y-2">
             <div className="flex justify-between text-sm"><span className="text-text-muted">P/E Ratio</span><span className="font-mono">{funds.pe_ratio ? funds.pe_ratio.toFixed(2) : '—'}</span></div>
             <div className="flex justify-between text-sm"><span className="text-text-muted">P/B Ratio</span><span className="font-mono">{funds.pb_ratio ? funds.pb_ratio.toFixed(2) : '—'}</span></div>
             <div className="flex justify-between text-sm"><span className="text-text-muted">ROE</span><span className="font-mono">{funds.roe ? (funds.roe * 100).toFixed(1) + '%' : '—'}</span></div>
             <div className="flex justify-between text-sm"><span className="text-text-muted">Div Yield</span><span className="font-mono">{funds.dividend_yield ? (funds.dividend_yield * 100).toFixed(1) + '%' : '—'}</span></div>
             <div className="flex justify-between text-sm"><span className="text-text-muted">Debt/Eq</span><span className="font-mono">{funds.debt_to_equity ? funds.debt_to_equity.toFixed(2) : '—'}</span></div>
          </div>
        </div>

        <div className="col-span-4 bg-bg-card border border-border rounded-lg p-4">
          <p className="text-[10px] uppercase tracking-wider text-text-muted font-mono mb-3">(C) Class Probabilities</p>
          <ProbBar label="BUY" value={probs.BUY || 0} color="text-buy" />
          <ProbBar label="HOLD" value={probs.HOLD || 0} color="text-text-primary" />
          <ProbBar label="SELL" value={probs.SELL || 0} color="text-sell" />
        </div>
      </div>

      {/* Row 2: Metrics */}
      <div className="grid grid-cols-5 gap-4">
        <MetricCard label="Regime Score" value={(regime.score || 0).toFixed(2)} />
        <MetricCard label="Volatility" value={`${((regime.volatility || 0) * 100).toFixed(1)}%`} />
        <MetricCard label="Sharpe" value={(btm.sharpe_ratio || 0).toFixed(2)} color={btm.sharpe_ratio > 0 ? 'text-accent' : 'text-sell'} />
        <MetricCard label="Max DD" value={`${((btm.max_drawdown || 0) * 100).toFixed(1)}%`} color="text-sell" />
        <MetricCard label="Win Rate" value={`${((btm.win_rate || 0) * 100).toFixed(0)}%`} />
      </div>

      {/* Row 3: Equity + Drivers */}
      <div className="grid grid-cols-12 gap-4">
        <div className="col-span-8 bg-bg-card border border-border rounded-lg p-4">
          <div className="flex justify-between items-center mb-3">
            <p className="text-[10px] uppercase tracking-wider text-text-muted font-mono">(D) Backtest Equity (Live Generative 2-Yr)</p>
            <div className="flex gap-4 text-[10px] font-mono">
              <span className="text-accent">— model</span><span className="text-text-muted">— benchmark</span>
            </div>
          </div>
          {chartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={chartData}>
                <XAxis dataKey="date" tick={{ fontSize: 9, fill: '#64748b' }} tickFormatter={(v: string) => v.slice(0, 7)} />
                <YAxis tick={{ fontSize: 9, fill: '#64748b' }} tickFormatter={(v: number) => `${(v/1000).toFixed(0)}k`} />
                <RechartsTooltip contentStyle={{ background: '#0d1b2a', border: '1px solid #1e3a5f', borderRadius: 8, fontSize: 11 }}
                  labelStyle={{ color: '#94a3b8' }} />
                <Line type="monotone" dataKey="strategy" stroke="#14b8a6" strokeWidth={1.5} dot={false} name="Model" />
                <Line type="monotone" dataKey="benchmark" stroke="#64748b" strokeWidth={1} dot={false} name="Buy & Hold" strokeDasharray="4 2" />
              </LineChart>
            </ResponsiveContainer>
          ) : <p className="text-text-muted text-sm h-48 flex items-center justify-center">No backtest data available.</p>}
        </div>
        
        <div className="col-span-4 bg-bg-card border border-border rounded-lg p-4">
          <p className="text-[10px] uppercase tracking-wider text-text-muted font-mono mb-3">(E) Current Feature Drivers</p>
          {drivers.length > 0 ? drivers.map((d: any) => <DriverBar key={d.feature} feature={d.feature} value={d.contribution} />)
            : <p className="text-text-muted text-sm">No feature data.</p>}
            
          <div className="mt-4 pt-4 border-t border-border">
              <p className="text-[10px] uppercase tracking-wider text-text-muted font-mono mb-3">Backtest Snapshot</p>
              <div className="grid grid-cols-2 gap-4">
                <div><p className="text-[10px] text-text-muted font-mono uppercase">Net P&L</p>
                  <p className={`text-xl font-bold font-mono ${(btm.cumulative_return||0) >= 0 ? 'text-buy' : 'text-sell'}`}>
                    {(btm.cumulative_return||0) >= 0 ? '+' : ''}{((btm.cumulative_return||0)*100).toFixed(1)}%</p></div>
                <div><p className="text-[10px] text-text-muted font-mono uppercase">Alpha</p>
                  <p className={`text-xl font-bold font-mono ${(btm.alpha||0) >= 0 ? 'text-buy' : 'text-sell'}`}>
                    {(btm.alpha||0) >= 0 ? '+' : ''}{((btm.alpha||0)*100).toFixed(1)}%</p></div>
              </div>
          </div>
        </div>
      </div>
    </div>
  );
}

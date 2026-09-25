import os
F = r'D:\PROJECTS\trademind\frontend\src'
def w(p, c):
    fp = os.path.join(F, p)
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    with open(fp, 'w', encoding='utf-8') as f: f.write(c)
    print(f'  {p}')

w('pages/OverviewPage.tsx', r"""import { useEffect, useState } from 'react';
import { api } from '../services/api';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { TrendingUp, TrendingDown, Minus, AlertCircle, Loader2, Play } from 'lucide-react';

function MetricCard({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div className="bg-bg-card border border-border rounded-lg p-3">
      <p className="text-[10px] uppercase tracking-wider text-text-muted font-mono mb-1">{label}</p>
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

export default function OverviewPage({ symbol }: { symbol: string }) {
  const [pred, setPred] = useState<any>(null);
  const [bt, setBt] = useState<any>(null);
  const [eq, setEq] = useState<any>(null);
  const [models, setModels] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [training, setTraining] = useState(false);
  const [trainMsg, setTrainMsg] = useState('');
  const [error, setError] = useState('');

  const load = () => {
    setLoading(true);
    setError('');
    Promise.all([
      api.getPrediction(symbol).catch(() => null),
      api.getBacktest(symbol).catch(() => null),
      api.getEquity(symbol).catch(() => null),
      api.getModelMetrics(symbol).catch(() => null),
    ]).then(([p, b, e, m]) => {
      setPred(p); setBt(b); setEq(e); setModels(m);
      if (!p && !b && !m) setError('no_model');
      setLoading(false);
    });
  };

  useEffect(() => { load(); }, [symbol]);

  const handleTrain = async () => {
    setTraining(true); setTrainMsg('Downloading dataset...');
    try {
      setTrainMsg('Training models — this may take 1-2 minutes...');
      const result = await api.train({ symbol, horizon: 5, threshold: 0.01, train_ratio: 0.70, validation_ratio: 0.15, use_regime: true });
      setTrainMsg('Training complete!');
      setTimeout(() => { setTraining(false); setTrainMsg(''); load(); }, 1000);
    } catch (e: any) {
      setTrainMsg(`Training failed: ${e.message}`);
      setTimeout(() => { setTraining(false); setTrainMsg(''); }, 3000);
    }
  };

  if (loading) return (
    <div className="flex items-center justify-center h-96"><Loader2 className="animate-spin text-accent" size={32} /><span className="ml-3 text-text-muted">Loading market data...</span></div>
  );

  if (error === 'no_model') return (
    <div className="flex flex-col items-center justify-center h-96 gap-4">
      <div className="w-16 h-16 rounded-2xl bg-accent/10 flex items-center justify-center"><AlertCircle className="text-accent" size={32} /></div>
      <h2 className="text-xl font-bold">Research Environment Not Initialized</h2>
      <p className="text-text-muted text-sm">No trained model available for {symbol}. Train models to begin analysis.</p>
      <button onClick={handleTrain} disabled={training}
        className="flex items-center gap-2 bg-accent hover:bg-accent-dim text-bg-primary px-6 py-2.5 rounded-lg font-medium transition-colors disabled:opacity-50">
        {training ? <Loader2 className="animate-spin" size={16} /> : <Play size={16} />}
        {training ? trainMsg : 'Train Models'}
      </button>
    </div>
  );

  const p = pred || {};
  const probs = p.probabilities || {};
  const regime = p.regime || {};
  const btm = bt?.metrics || {};
  const eqData = eq?.equity_curve || [];
  const mods = models?.models || {};
  const bestModel = models?.best_model || '';
  const drivers = (p.feature_drivers || []).slice(0, 4);

  // Format equity for chart (sample every nth point for performance)
  const step = Math.max(1, Math.floor(eqData.length / 200));
  const chartData = eqData.filter((_: any, i: number) => i % step === 0 || i === eqData.length - 1);

  return (
    <div className="space-y-4">
      {training && <div className="bg-accent/10 border border-accent/30 rounded-lg p-3 flex items-center gap-2 text-sm text-accent"><Loader2 className="animate-spin" size={14} />{trainMsg}</div>}

      {/* Row 1: Signal + Probabilities */}
      <div className="grid grid-cols-12 gap-4">
        <div className="col-span-8 bg-bg-card border border-border rounded-lg p-4">
          <div className="flex justify-between items-start mb-3">
            <p className="text-[10px] uppercase tracking-wider text-text-muted font-mono">(A) Signal Summary</p>
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
        <div className="col-span-4 bg-bg-card border border-border rounded-lg p-4">
          <p className="text-[10px] uppercase tracking-wider text-text-muted font-mono mb-3">(B) Class Probabilities</p>
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
            <p className="text-[10px] uppercase tracking-wider text-text-muted font-mono">(C) Backtest Equity · Buy-and-Hold vs Model</p>
            <div className="flex gap-4 text-[10px] font-mono">
              <span className="text-accent">— model</span><span className="text-text-muted">— benchmark</span>
            </div>
          </div>
          {chartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={chartData}>
                <XAxis dataKey="date" tick={{ fontSize: 9, fill: '#64748b' }} tickFormatter={(v: string) => v.slice(0, 7)} />
                <YAxis tick={{ fontSize: 9, fill: '#64748b' }} tickFormatter={(v: number) => `${(v/1000).toFixed(0)}k`} />
                <Tooltip contentStyle={{ background: '#0d1b2a', border: '1px solid #1e3a5f', borderRadius: 8, fontSize: 11 }}
                  labelStyle={{ color: '#94a3b8' }} />
                <Line type="monotone" dataKey="strategy" stroke="#14b8a6" strokeWidth={1.5} dot={false} name="Model" />
                <Line type="monotone" dataKey="benchmark" stroke="#64748b" strokeWidth={1} dot={false} name="Benchmark" strokeDasharray="4 2" />
              </LineChart>
            </ResponsiveContainer>
          ) : <p className="text-text-muted text-sm h-48 flex items-center justify-center">No backtest data available.</p>}
        </div>
        <div className="col-span-4 bg-bg-card border border-border rounded-lg p-4">
          <p className="text-[10px] uppercase tracking-wider text-text-muted font-mono mb-3">(D) Feature Drivers</p>
          {drivers.length > 0 ? drivers.map((d: any) => <DriverBar key={d.feature} feature={d.feature} value={d.contribution} />)
            : <p className="text-text-muted text-sm">No feature data.</p>}
        </div>
      </div>

      {/* Row 4: Model Comparison + Backtest Snapshot */}
      <div className="grid grid-cols-12 gap-4">
        <div className="col-span-7 bg-bg-card border border-border rounded-lg p-4">
          <div className="flex justify-between items-center mb-3">
            <p className="text-[10px] uppercase tracking-wider text-text-muted font-mono">(E) Model Comparison</p>
            <p className="text-[10px] text-text-muted font-mono">chronological test</p>
          </div>
          <table className="w-full text-xs">
            <thead><tr className="text-text-muted font-mono uppercase tracking-wider">
              <th className="text-left py-1">Model</th><th className="text-right">Acc</th><th className="text-right">F1</th><th className="text-right">ROC-AUC</th>
            </tr></thead>
            <tbody>{Object.entries(mods).map(([name, data]: [string, any]) => {
              const tm = data?.test_metrics || data?.test || {};
              const isBest = name === bestModel;
              return (
                <tr key={name} className={`border-t border-border/50 ${isBest ? 'bg-accent/5' : ''}`}>
                  <td className={`py-2 ${isBest ? 'text-accent font-medium' : 'text-text-primary'}`}>{name}</td>
                  <td className="text-right font-mono text-text-secondary">{((tm.accuracy||0)*100).toFixed(0)}%</td>
                  <td className="text-right font-mono text-text-secondary">{(tm.f1_weighted||0).toFixed(2)}</td>
                  <td className="text-right font-mono text-text-secondary">{tm.roc_auc ? tm.roc_auc.toFixed(2) : '—'}</td>
                </tr>
              );
            })}</tbody>
          </table>
        </div>
        <div className="col-span-5 bg-bg-card border border-border rounded-lg p-4">
          <p className="text-[10px] uppercase tracking-wider text-text-muted font-mono mb-3">(F) Backtest Snapshot</p>
          <div className="grid grid-cols-2 gap-4">
            <div><p className="text-[10px] text-text-muted font-mono uppercase">Net P&L</p>
              <p className={`text-xl font-bold font-mono ${(btm.cumulative_return||0) >= 0 ? 'text-buy' : 'text-sell'}`}>
                {(btm.cumulative_return||0) >= 0 ? '+' : ''}{((btm.cumulative_return||0)*100).toFixed(1)}%</p></div>
            <div><p className="text-[10px] text-text-muted font-mono uppercase">Alpha</p>
              <p className={`text-xl font-bold font-mono ${(btm.alpha||0) >= 0 ? 'text-buy' : 'text-sell'}`}>
                {(btm.alpha||0) >= 0 ? '+' : ''}{((btm.alpha||0)*100).toFixed(1)}%</p></div>
            <div><p className="text-[10px] text-text-muted font-mono uppercase">Trades</p>
              <p className="text-xl font-bold font-mono text-text-primary">{btm.total_trades || 0}</p></div>
            <div><p className="text-[10px] text-text-muted font-mono uppercase">Period</p>
              <p className="text-sm font-bold font-mono text-text-primary">{btm.period_start?.slice(0,4)||'—'}–{btm.period_end?.slice(0,4)||''}</p></div>
          </div>
        </div>
      </div>
    </div>
  );
}
""")

print('Overview page done')
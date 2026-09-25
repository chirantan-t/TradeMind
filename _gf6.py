import os
F = r'D:\PROJECTS\trademind\frontend\src'
def w(p, c):
    fp = os.path.join(F, p)
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    with open(fp, 'w', encoding='utf-8') as f: f.write(c)
    print(f'  {p}')

w('pages/BacktestPage.tsx', r"""import { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Loader2, Play } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';

export default function BacktestPage({ symbol }: { symbol: string }) {
  const [bt, setBt] = useState<any>(null);
  const [eq, setEq] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [config, setConfig] = useState({ initial_capital: 100000, transaction_cost: 0.001, slippage: 0.0005, position_mode: 'long_short' });

  const load = () => {
    setLoading(true);
    Promise.all([
      api.getBacktest(symbol).catch(() => null),
      api.getEquity(symbol).catch(() => null),
    ]).then(([b, e]) => { setBt(b); setEq(e); setLoading(false); });
  };
  useEffect(() => { load(); }, [symbol]);

  const handleRun = async () => {
    setRunning(true);
    try {
      const result = await api.runBacktest({ symbol, ...config });
      setBt({ metrics: result.metrics, config: result.config });
      setEq({ equity_curve: result.equity_curve, trades: result.trades });
      setRunning(false);
    } catch (e: any) { alert(`Backtest failed: ${e.message}`); setRunning(false); }
  };

  if (loading) return <div className="flex items-center justify-center h-96"><Loader2 className="animate-spin text-accent" size={32}/></div>;
  const m = bt?.metrics || {};
  const eqData = eq?.equity_curve || [];
  const trades = eq?.trades || [];
  const step = Math.max(1, Math.floor(eqData.length / 200));
  const chartData = eqData.filter((_: any, i: number) => i % step === 0 || i === eqData.length - 1);
  const ddData = chartData.map((d: any) => ({ ...d, dd: d.drawdown * 100 }));
  const currency = bt?.config?.currency === 'INR' ? '₹' : '$';

  return (
    <div className="space-y-4">
      {/* Config */}
      <div className="bg-bg-card border border-border rounded-lg p-4">
        <div className="flex items-center justify-between mb-3">
          <p className="text-[10px] uppercase tracking-wider text-text-muted font-mono">Backtest Configuration</p>
          <button onClick={handleRun} disabled={running}
            className="flex items-center gap-2 bg-accent hover:bg-accent-dim text-bg-primary px-4 py-1.5 rounded-lg text-sm font-medium disabled:opacity-50">
            {running ? <Loader2 className="animate-spin" size={14}/> : <Play size={14}/>} Run Backtest
          </button>
        </div>
        <div className="grid grid-cols-4 gap-4 text-xs">
          <div><label className="text-text-muted block mb-1">Initial Capital</label>
            <input type="number" value={config.initial_capital} onChange={e => setConfig({...config, initial_capital: +e.target.value})}
              className="w-full bg-bg-primary border border-border rounded px-2 py-1 text-text-primary font-mono"/></div>
          <div><label className="text-text-muted block mb-1">Transaction Cost</label>
            <input type="number" step="0.0001" value={config.transaction_cost} onChange={e => setConfig({...config, transaction_cost: +e.target.value})}
              className="w-full bg-bg-primary border border-border rounded px-2 py-1 text-text-primary font-mono"/></div>
          <div><label className="text-text-muted block mb-1">Slippage</label>
            <input type="number" step="0.0001" value={config.slippage} onChange={e => setConfig({...config, slippage: +e.target.value})}
              className="w-full bg-bg-primary border border-border rounded px-2 py-1 text-text-primary font-mono"/></div>
          <div><label className="text-text-muted block mb-1">Position Mode</label>
            <select value={config.position_mode} onChange={e => setConfig({...config, position_mode: e.target.value})}
              className="w-full bg-bg-primary border border-border rounded px-2 py-1 text-text-primary font-mono">
              <option value="long_short">Long/Short</option><option value="long_only">Long Only</option>
            </select></div>
        </div>
      </div>

      {/* Equity Curve */}
      <div className="bg-bg-card border border-border rounded-lg p-4">
        <p className="text-[10px] uppercase tracking-wider text-text-muted font-mono mb-3">Equity Curve — Strategy vs Benchmark</p>
        {chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={chartData}>
              <XAxis dataKey="date" tick={{ fontSize: 9, fill: '#64748b' }} tickFormatter={(v: string) => v.slice(0,7)} />
              <YAxis tick={{ fontSize: 9, fill: '#64748b' }} tickFormatter={(v: number) => `${currency}${(v/1000).toFixed(0)}k`} />
              <Tooltip contentStyle={{ background: '#0d1b2a', border: '1px solid #1e3a5f', borderRadius: 8, fontSize: 11 }} />
              <Line type="monotone" dataKey="strategy" stroke="#14b8a6" strokeWidth={2} dot={false} name="Strategy" />
              <Line type="monotone" dataKey="benchmark" stroke="#64748b" strokeWidth={1} dot={false} name="Buy & Hold" strokeDasharray="4 2" />
            </LineChart>
          </ResponsiveContainer>
        ) : <p className="text-text-muted text-sm h-48 flex items-center justify-center">Run backtest to see equity curve.</p>}
      </div>

      {/* Drawdown */}
      {ddData.length > 0 && (
        <div className="bg-bg-card border border-border rounded-lg p-4">
          <p className="text-[10px] uppercase tracking-wider text-text-muted font-mono mb-3">Drawdown</p>
          <ResponsiveContainer width="100%" height={120}>
            <AreaChart data={ddData}>
              <XAxis dataKey="date" tick={{ fontSize: 9, fill: '#64748b' }} tickFormatter={(v: string) => v.slice(0,7)} />
              <YAxis tick={{ fontSize: 9, fill: '#64748b' }} tickFormatter={(v: number) => `${v.toFixed(0)}%`} />
              <Tooltip contentStyle={{ background: '#0d1b2a', border: '1px solid #1e3a5f', borderRadius: 8, fontSize: 11 }} />
              <Area type="monotone" dataKey="dd" stroke="#ef4444" fill="#ef4444" fillOpacity={0.15} name="Drawdown %" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Metrics */}
      {m.cumulative_return !== undefined && (
        <div className="grid grid-cols-5 gap-4">
          {[
            { label: 'Net Return', value: `${(m.cumulative_return*100).toFixed(1)}%`, color: m.cumulative_return >= 0 ? 'text-buy' : 'text-sell' },
            { label: 'Annualized', value: `${(m.annualized_return*100).toFixed(1)}%`, color: m.annualized_return >= 0 ? 'text-buy' : 'text-sell' },
            { label: 'Sharpe', value: m.sharpe_ratio.toFixed(2), color: m.sharpe_ratio > 0 ? 'text-accent' : 'text-sell' },
            { label: 'Max Drawdown', value: `${(m.max_drawdown*100).toFixed(1)}%`, color: 'text-sell' },
            { label: 'Win Rate', value: `${(m.win_rate*100).toFixed(0)}%`, color: '' },
          ].map(({ label, value, color }) => (
            <div key={label} className="bg-bg-card border border-border rounded-lg p-3">
              <p className="text-[10px] uppercase tracking-wider text-text-muted font-mono mb-1">{label}</p>
              <p className={`text-lg font-bold font-mono ${color}`}>{value}</p>
            </div>
          ))}
        </div>
      )}

      {/* Detailed metrics table */}
      {m.cumulative_return !== undefined && (
        <div className="bg-bg-card border border-border rounded-lg p-4">
          <p className="text-[10px] uppercase tracking-wider text-text-muted font-mono mb-3">Detailed Metrics</p>
          <div className="grid grid-cols-3 gap-x-8 gap-y-2 text-xs">
            {[
              ['Total Trades', m.total_trades],
              ['Alpha vs B&H', `${(m.alpha*100).toFixed(2)}%`],
              ['Volatility', `${(m.volatility*100).toFixed(1)}%`],
              ['Transaction Costs', `${currency}${m.total_transaction_costs?.toFixed(2)}`],
              ['Slippage', `${currency}${m.total_slippage?.toFixed(2)}`],
              ['Net P&L', `${currency}${m.net_pnl?.toFixed(2)}`],
              ['Final Equity', `${currency}${m.final_equity?.toFixed(2)}`],
              ['Period', `${m.period_start} → ${m.period_end}`],
              ['Trading Days', m.trading_days],
            ].map(([l, v]) => (
              <div key={l as string} className="flex justify-between py-1 border-b border-border/30">
                <span className="text-text-muted">{l}</span>
                <span className="font-mono text-text-primary">{v}</span>
              </div>
            ))}
          </div>
          <p className="text-[10px] text-text-muted mt-3 italic">Historical simulation only. Past performance does not indicate future results.</p>
        </div>
      )}
    </div>
  );
}
""")

print('Backtest page done')
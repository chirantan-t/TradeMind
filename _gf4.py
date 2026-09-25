import os
F = r'D:\PROJECTS\trademind\frontend\src'
def w(p, c):
    fp = os.path.join(F, p)
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    with open(fp, 'w', encoding='utf-8') as f: f.write(c)
    print(f'  {p}')

w('pages/SignalsPage.tsx', r"""import { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Loader2 } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar, Cell } from 'recharts';

const SIG_COLORS: Record<string, string> = { BUY: '#10b981', HOLD: '#f59e0b', SELL: '#ef4444' };

export default function SignalsPage({ symbol }: { symbol: string }) {
  const [pred, setPred] = useState<any>(null);
  const [signals, setSignals] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<any>(null);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      api.getPrediction(symbol).catch(() => null),
      api.getSignals(symbol).catch(() => ({ signals: [] })),
    ]).then(([p, s]) => {
      setPred(p);
      setSignals(s?.signals || []);
      setLoading(false);
    });
  }, [symbol]);

  if (loading) return <div className="flex items-center justify-center h-96"><Loader2 className="animate-spin text-accent" size={32} /></div>;
  if (!pred) return <div className="text-center text-text-muted mt-20">No predictions available. Train models first.</div>;

  const p = pred;
  const probs = p.probabilities || {};
  const regime = p.regime || {};
  const drivers = (p.feature_drivers || []).slice(0, 8);
  const sel = selected || p;

  const probData = [
    { name: 'BUY', value: probs.BUY || 0 },
    { name: 'HOLD', value: probs.HOLD || 0 },
    { name: 'SELL', value: probs.SELL || 0 },
  ];

  return (
    <div className="space-y-4">
      {/* Current Signal Detail */}
      <div className="grid grid-cols-12 gap-4">
        <div className="col-span-5 bg-bg-card border border-border rounded-lg p-4">
          <p className="text-[10px] uppercase tracking-wider text-text-muted font-mono mb-2">Current Signal</p>
          <div className="flex items-center gap-3 mb-3">
            <span className={`text-4xl font-bold font-mono ${p.signal === 'BUY' ? 'text-buy' : p.signal === 'SELL' ? 'text-sell' : 'text-hold'}`}>{p.signal}</span>
            <div>
              <p className="text-xs text-text-muted font-mono">Confidence: {(p.confidence*100).toFixed(1)}%</p>
              <p className="text-xs text-text-muted font-mono">Model: {p.model}</p>
              <p className="text-xs text-text-muted font-mono">Date: {p.date}</p>
            </div>
          </div>
          <p className="text-xs text-text-secondary">{p.explanation}</p>
        </div>
        <div className="col-span-3 bg-bg-card border border-border rounded-lg p-4">
          <p className="text-[10px] uppercase tracking-wider text-text-muted font-mono mb-2">Probabilities</p>
          <ResponsiveContainer width="100%" height={140}>
            <BarChart data={probData} layout="vertical">
              <XAxis type="number" domain={[0, 1]} tick={{ fontSize: 9 }} />
              <YAxis type="category" dataKey="name" tick={{ fontSize: 10, fill: '#e2e8f0' }} width={40} />
              <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                {probData.map((d, i) => <Cell key={i} fill={SIG_COLORS[d.name] || '#64748b'} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="col-span-4 bg-bg-card border border-border rounded-lg p-4">
          <p className="text-[10px] uppercase tracking-wider text-text-muted font-mono mb-2">Regime</p>
          <div className="space-y-2">
            <div className="flex justify-between"><span className="text-xs text-text-muted">Label</span>
              <span className={`text-xs font-bold font-mono ${regime.label === 'BULL' ? 'text-buy' : regime.label === 'BEAR' ? 'text-sell' : 'text-text-muted'}`}>{regime.label}</span></div>
            <div className="flex justify-between"><span className="text-xs text-text-muted">Score</span><span className="text-xs font-mono">{(regime.score||0).toFixed(2)}</span></div>
            <div className="flex justify-between"><span className="text-xs text-text-muted">Volatility</span><span className="text-xs font-mono">{((regime.volatility||0)*100).toFixed(1)}%</span></div>
          </div>
        </div>
      </div>

      {/* Feature Drivers */}
      <div className="bg-bg-card border border-border rounded-lg p-4">
        <p className="text-[10px] uppercase tracking-wider text-text-muted font-mono mb-3">Feature Contributions</p>
        <div className="grid grid-cols-2 gap-x-8 gap-y-1">
          {drivers.map((d: any) => (
            <div key={d.feature} className="flex items-center gap-2 py-1">
              <span className="text-xs text-text-secondary w-36 truncate">{d.feature.replace(/_/g, ' ')}</span>
              <div className="flex-1 h-1.5 bg-bg-primary rounded-full overflow-hidden">
                <div className={`h-full rounded-full ${d.contribution >= 0 ? 'bg-accent' : 'bg-sell'}`}
                  style={{ width: `${Math.min(Math.abs(d.contribution) * 400, 100)}%` }} /></div>
              <span className={`text-xs font-mono w-14 text-right ${d.contribution >= 0 ? 'text-accent' : 'text-sell'}`}>
                {d.contribution > 0 ? '+' : ''}{d.contribution.toFixed(3)}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Signal Timeline */}
      <div className="bg-bg-card border border-border rounded-lg p-4">
        <p className="text-[10px] uppercase tracking-wider text-text-muted font-mono mb-3">Signal History</p>
        {signals.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead><tr className="text-text-muted font-mono uppercase">
                <th className="text-left py-1 px-2">Date</th><th className="text-left">Signal</th>
                <th className="text-right">Confidence</th><th className="text-right">Close</th>
                <th className="text-right">Buy%</th><th className="text-right">Hold%</th><th className="text-right">Sell%</th>
                <th className="text-left px-2">Regime</th>
              </tr></thead>
              <tbody>{signals.slice(0, 30).map((s: any) => (
                <tr key={s.date} className="border-t border-border/30 hover:bg-bg-card-hover cursor-pointer" onClick={() => setSelected(s)}>
                  <td className="py-1.5 px-2 font-mono">{s.date}</td>
                  <td><span className={`font-bold ${s.signal === 'BUY' ? 'text-buy' : s.signal === 'SELL' ? 'text-sell' : 'text-hold'}`}>{s.signal}</span></td>
                  <td className="text-right font-mono">{(s.confidence*100).toFixed(0)}%</td>
                  <td className="text-right font-mono">{s.close?.toFixed(2)}</td>
                  <td className="text-right font-mono text-buy">{(s.prob_buy*100).toFixed(0)}%</td>
                  <td className="text-right font-mono">{(s.prob_hold*100).toFixed(0)}%</td>
                  <td className="text-right font-mono text-sell">{(s.prob_sell*100).toFixed(0)}%</td>
                  <td className={`px-2 font-mono ${s.regime === 'BULL' ? 'text-buy' : s.regime === 'BEAR' ? 'text-sell' : 'text-text-muted'}`}>{s.regime}</td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        ) : <p className="text-text-muted text-sm">No signal history available.</p>}
      </div>
    </div>
  );
}
""")

print('Signals page done')
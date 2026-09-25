import os
F = r'D:\PROJECTS\trademind\frontend\src'
def w(p, c):
    fp = os.path.join(F, p)
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    with open(fp, 'w', encoding='utf-8') as f: f.write(c)
    print(f'  {p}')

w('pages/DataPage.tsx', r"""import { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Loader2, RefreshCw } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

export default function DataPage({ symbol }: { symbol: string }) {
  const [data, setData] = useState<any>(null);
  const [prices, setPrices] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = () => {
    setLoading(true);
    Promise.all([
      api.getDatasetSummary(symbol).catch(() => null),
      api.getPrices(symbol, 200).catch(() => ({ prices: [] })),
    ]).then(([d, p]) => {
      setData(d);
      setPrices(p?.prices || []);
      setLoading(false);
    });
  };
  useEffect(() => { load(); }, [symbol]);

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await api.refreshData(symbol);
      load();
    } catch (e) {
      console.error(e);
    } finally {
      setRefreshing(false);
    }
  };

  if (loading) return <div className="flex items-center justify-center h-96"><Loader2 className="animate-spin text-accent" size={32}/></div>;
  if (!data) return <div className="text-center text-text-muted mt-20">No data available for {symbol}.</div>;

  const currency = data.currency === 'INR' ? '₹' : '$';

  return (
    <div className="space-y-4">
      {/* Overview & Quality */}
      <div className="grid grid-cols-12 gap-4">
        <div className="col-span-8 bg-bg-card border border-border rounded-lg p-4">
          <div className="flex justify-between items-center mb-4">
            <div>
              <p className="text-[10px] uppercase tracking-wider text-text-muted font-mono">Dataset Overview</p>
              <h2 className="text-lg font-bold mt-1 text-text-primary">{data.name} ({symbol})</h2>
            </div>
            <button onClick={handleRefresh} disabled={refreshing}
              className="flex items-center gap-2 bg-accent/10 hover:bg-accent/20 text-accent border border-accent/30 px-3 py-1.5 rounded-md text-sm transition-colors disabled:opacity-50">
              <RefreshCw size={14} className={refreshing ? 'animate-spin' : ''}/> Refresh
            </button>
          </div>
          <div className="grid grid-cols-4 gap-4 mb-4">
            <div><p className="text-[10px] text-text-muted font-mono uppercase">Source</p><p className="font-mono text-sm">{data.source}</p></div>
            <div><p className="text-[10px] text-text-muted font-mono uppercase">Period Start</p><p className="font-mono text-sm">{data.start}</p></div>
            <div><p className="text-[10px] text-text-muted font-mono uppercase">Period End</p><p className="font-mono text-sm">{data.end}</p></div>
            <div><p className="text-[10px] text-text-muted font-mono uppercase">Total Rows</p><p className="font-mono text-sm">{data.rows}</p></div>
          </div>
          <div className="grid grid-cols-4 gap-4 pt-3 border-t border-border/50">
            <div><p className="text-[10px] text-text-muted font-mono uppercase">Features Built</p><p className="font-mono text-sm">{data.feature_count || 0}</p></div>
            <div><p className="text-[10px] text-text-muted font-mono uppercase">Missing Values</p><p className={`font-mono text-sm ${data.missing_values === 0 ? 'text-buy' : 'text-sell'}`}>{data.missing_values}</p></div>
            <div><p className="text-[10px] text-text-muted font-mono uppercase">Invalid OHLC</p><p className={`font-mono text-sm ${data.invalid_ohlc === 0 ? 'text-buy' : 'text-sell'}`}>{data.invalid_ohlc}</p></div>
            <div><p className="text-[10px] text-text-muted font-mono uppercase">Duplicate Dates</p><p className={`font-mono text-sm ${data.duplicate_dates === 0 ? 'text-buy' : 'text-sell'}`}>{data.duplicate_dates}</p></div>
          </div>
        </div>
        
        {/* Class Distribution */}
        <div className="col-span-4 bg-bg-card border border-border rounded-lg p-4">
          <p className="text-[10px] uppercase tracking-wider text-text-muted font-mono mb-3">Target Distribution</p>
          {data.class_distribution && Object.keys(data.class_distribution).length > 0 ? (
            <div className="space-y-3">
              {[
                { label: 'BUY', count: data.class_distribution[0], color: 'text-buy' },
                { label: 'HOLD', count: data.class_distribution[1], color: 'text-text-primary' },
                { label: 'SELL', count: data.class_distribution[2], color: 'text-sell' },
              ].map(({ label, count, color }) => {
                const total = (data.class_distribution[0]||0) + (data.class_distribution[1]||0) + (data.class_distribution[2]||0);
                const pct = total > 0 ? (count / total) * 100 : 0;
                return (
                  <div key={label}>
                    <div className="flex justify-between text-xs mb-1">
                      <span className={color}>{label}</span>
                      <span className="text-text-secondary font-mono">{count} ({pct.toFixed(1)}%)</span>
                    </div>
                    <div className="h-1.5 bg-bg-primary rounded-full overflow-hidden">
                      <div className={`h-full rounded-full ${color.replace('text-', 'bg-')}`} style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                );
              })}
            </div>
          ) : <p className="text-text-muted text-sm mt-4">Target not yet generated. Train a model to see distribution.</p>}
        </div>
      </div>

      {/* Price Chart */}
      <div className="bg-bg-card border border-border rounded-lg p-4">
        <p className="text-[10px] uppercase tracking-wider text-text-muted font-mono mb-3">Recent Price History</p>
        {prices.length > 0 ? (
          <ResponsiveContainer width="100%" height={280}>
            <AreaChart data={prices}>
              <XAxis dataKey="date" tick={{ fontSize: 9, fill: '#64748b' }} tickFormatter={(v: string) => v.slice(0, 7)} />
              <YAxis tick={{ fontSize: 9, fill: '#64748b' }} domain={['auto', 'auto']} tickFormatter={(v: number) => `${currency}${(v/1000).toFixed(1)}k`} />
              <Tooltip contentStyle={{ background: '#0d1b2a', border: '1px solid #1e3a5f', borderRadius: 8, fontSize: 11 }} />
              <Area type="monotone" dataKey="close" stroke="#0ea5e9" fill="#0ea5e9" fillOpacity={0.1} name="Close Price" />
            </AreaChart>
          </ResponsiveContainer>
        ) : <p className="text-text-muted text-sm h-48 flex items-center justify-center">No price data available.</p>}
      </div>
      
      {/* Raw Data Preview */}
      <div className="bg-bg-card border border-border rounded-lg p-4">
        <p className="text-[10px] uppercase tracking-wider text-text-muted font-mono mb-3">Recent Records</p>
        {prices.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-right">
              <thead><tr className="text-text-muted font-mono uppercase border-b border-border">
                <th className="text-left py-2 px-2">Date</th><th>Open</th><th>High</th><th>Low</th><th>Close</th><th>Volume</th>
              </tr></thead>
              <tbody>{prices.slice(-10).reverse().map((r: any) => (
                <tr key={r.date} className="border-b border-border/30 hover:bg-bg-card-hover">
                  <td className="text-left py-1.5 px-2 font-mono">{r.date}</td>
                  <td className="font-mono">{r.open.toFixed(2)}</td><td className="font-mono">{r.high.toFixed(2)}</td>
                  <td className="font-mono">{r.low.toFixed(2)}</td><td className="font-mono">{r.close.toFixed(2)}</td>
                  <td className="font-mono">{(r.volume/1000000).toFixed(2)}M</td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        ) : <p className="text-text-muted text-sm">No data available.</p>}
      </div>
    </div>
  );
}
""")

print('DataPage done')
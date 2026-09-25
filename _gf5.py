import os
F = r'D:\PROJECTS\trademind\frontend\src'
def w(p, c):
    fp = os.path.join(F, p)
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    with open(fp, 'w', encoding='utf-8') as f: f.write(c)
    print(f'  {p}')

w('pages/ModelLabPage.tsx', r"""import { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Loader2, Play, Trophy, Clock } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, RadarChart, PolarGrid, PolarAngleAxis, Radar } from 'recharts';

const MODEL_COLORS: Record<string, string> = {
  LogisticRegression: '#8b5cf6', RandomForest: '#06b6d4',
  GradientBoosting: '#f59e0b', SVM: '#ec4899'
};

export default function ModelLabPage({ symbol }: { symbol: string }) {
  const [data, setData] = useState<any>(null);
  const [comp, setComp] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [training, setTraining] = useState(false);
  const [trainMsg, setTrainMsg] = useState('');
  const [explainData, setExplainData] = useState<any>(null);

  const load = () => {
    setLoading(true);
    Promise.all([
      api.getModelMetrics(symbol).catch(() => null),
      api.getModelComparison(symbol).catch(() => null),
      api.getExplanation(symbol).catch(() => null),
    ]).then(([d, c, e]) => {
      setData(d); setComp(c); setExplainData(e); setLoading(false);
    });
  };
  useEffect(() => { load(); }, [symbol]);

  const handleTrain = async () => {
    setTraining(true); setTrainMsg('Training all models...');
    try {
      await api.train({ symbol, horizon: 5, threshold: 0.01, train_ratio: 0.70, validation_ratio: 0.15, use_regime: true });
      setTrainMsg('Complete!'); setTimeout(() => { setTraining(false); setTrainMsg(''); load(); }, 1000);
    } catch (e: any) { setTrainMsg(`Failed: ${e.message}`); setTimeout(() => { setTraining(false); }, 3000); }
  };

  if (loading) return <div className="flex items-center justify-center h-96"><Loader2 className="animate-spin text-accent" size={32} /></div>;
  if (!data) return (
    <div className="text-center mt-20">
      <p className="text-text-muted mb-4">No trained models. Train models to see results.</p>
      <button onClick={handleTrain} disabled={training} className="bg-accent hover:bg-accent-dim text-bg-primary px-6 py-2 rounded-lg font-medium flex items-center gap-2 mx-auto">
        {training ? <Loader2 className="animate-spin" size={16}/> : <Play size={16}/>} {training ? trainMsg : 'Train Models'}
      </button>
    </div>
  );

  const models = data.models || {};
  const best = data.best_model || '';
  const splitInfo = comp?.split_info || {};
  const globalImp = (explainData?.global_importance || []).slice(0, 10);

  const compData = Object.entries(models).map(([name, m]: [string, any]) => {
    const tm = m.test_metrics || m.test || {};
    return { name, accuracy: (tm.accuracy||0)*100, f1: (tm.f1_weighted||0)*100,
             roc_auc: (tm.roc_auc||0)*100, train_time: m.train_time||0 };
  });

  return (
    <div className="space-y-4">
      {training && <div className="bg-accent/10 border border-accent/30 rounded-lg p-3 flex items-center gap-2 text-sm text-accent"><Loader2 className="animate-spin" size={14}/>{trainMsg}</div>}

      {/* Model Cards */}
      <div className="grid grid-cols-4 gap-4">
        {Object.entries(models).map(([name, m]: [string, any]) => {
          const vm = m.val_metrics || m.val || {};
          const tm = m.test_metrics || m.test || {};
          const isBest = name === best;
          return (
            <div key={name} className={`bg-bg-card border rounded-lg p-4 ${isBest ? 'border-accent' : 'border-border'}`}>
              <div className="flex justify-between items-start mb-3">
                <h3 className={`text-sm font-medium ${isBest ? 'text-accent' : 'text-text-primary'}`}>{name}</h3>
                {isBest && <Trophy size={14} className="text-accent" />}
              </div>
              <div className="space-y-1.5 text-xs">
                <div className="flex justify-between"><span className="text-text-muted">Accuracy</span><span className="font-mono">{((tm.accuracy||0)*100).toFixed(1)}%</span></div>
                <div className="flex justify-between"><span className="text-text-muted">F1 (weighted)</span><span className="font-mono">{(tm.f1_weighted||0).toFixed(3)}</span></div>
                <div className="flex justify-between"><span className="text-text-muted">ROC-AUC</span><span className="font-mono">{tm.roc_auc ? tm.roc_auc.toFixed(3) : '—'}</span></div>
                <div className="flex justify-between"><span className="text-text-muted">Train time</span><span className="font-mono flex items-center gap-1"><Clock size={10}/>{(m.train_time||0).toFixed(1)}s</span></div>
              </div>
              {/* Mini confusion matrix */}
              {tm.confusion_matrix && (
                <div className="mt-3 pt-2 border-t border-border/50">
                  <p className="text-[9px] text-text-muted font-mono mb-1">Confusion Matrix</p>
                  <div className="grid grid-cols-3 gap-0.5 text-[9px] font-mono text-center">
                    {tm.confusion_matrix.map((row: number[], ri: number) =>
                      row.map((v: number, ci: number) => (
                        <div key={`${ri}-${ci}`} className={`p-1 rounded ${ri === ci ? 'bg-accent/20 text-accent' : 'bg-bg-primary text-text-muted'}`}>{v}</div>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Comparison Chart + Feature Importance */}
      <div className="grid grid-cols-12 gap-4">
        <div className="col-span-7 bg-bg-card border border-border rounded-lg p-4">
          <p className="text-[10px] uppercase tracking-wider text-text-muted font-mono mb-3">Model Comparison (Test Set)</p>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={compData}>
              <XAxis dataKey="name" tick={{ fontSize: 9, fill: '#94a3b8' }} />
              <YAxis tick={{ fontSize: 9, fill: '#64748b' }} />
              <Tooltip contentStyle={{ background: '#0d1b2a', border: '1px solid #1e3a5f', borderRadius: 8, fontSize: 11 }} />
              <Bar dataKey="accuracy" name="Accuracy %" radius={[4,4,0,0]}>
                {compData.map((d, i) => <Cell key={i} fill={MODEL_COLORS[d.name] || '#64748b'} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="col-span-5 bg-bg-card border border-border rounded-lg p-4">
          <p className="text-[10px] uppercase tracking-wider text-text-muted font-mono mb-3">Global Feature Importance</p>
          {globalImp.length > 0 ? (
            <div className="space-y-1.5">
              {globalImp.map((d: any, i: number) => (
                <div key={i} className="flex items-center gap-2">
                  <span className="text-[10px] text-text-secondary w-32 truncate">{d.feature.replace(/_/g, ' ')}</span>
                  <div className="flex-1 h-1 bg-bg-primary rounded-full"><div className="h-full bg-accent rounded-full" style={{ width: `${Math.min((d.importance / (globalImp[0]?.importance || 1)) * 100, 100)}%` }} /></div>
                  <span className="text-[10px] font-mono text-text-muted w-10 text-right">{d.importance.toFixed(3)}</span>
                </div>
              ))}
            </div>
          ) : <p className="text-text-muted text-sm">Not available.</p>}
        </div>
      </div>

      {/* Training Config + Split Info */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-bg-card border border-border rounded-lg p-4">
          <p className="text-[10px] uppercase tracking-wider text-text-muted font-mono mb-2">Data Split</p>
          <div className="space-y-1 text-xs">
            <div className="flex justify-between"><span className="text-text-muted">Train</span><span className="font-mono">{splitInfo.train_start} → {splitInfo.train_end} ({splitInfo.train_samples} samples)</span></div>
            <div className="flex justify-between"><span className="text-text-muted">Validation</span><span className="font-mono">{splitInfo.val_start} → {splitInfo.val_end} ({splitInfo.val_samples})</span></div>
            <div className="flex justify-between"><span className="text-text-muted">Test</span><span className="font-mono">{splitInfo.test_start} → {splitInfo.test_end} ({splitInfo.test_samples})</span></div>
          </div>
        </div>
        <div className="bg-bg-card border border-border rounded-lg p-4">
          <p className="text-[10px] uppercase tracking-wider text-text-muted font-mono mb-2">Training Configuration</p>
          <div className="space-y-1 text-xs">
            <div className="flex justify-between"><span className="text-text-muted">Features</span><span className="font-mono">{data.feature_count || '—'}</span></div>
            <div className="flex justify-between"><span className="text-text-muted">Best model</span><span className="font-mono text-accent">{best}</span></div>
            <div className="flex justify-between"><span className="text-text-muted">Regime features</span><span className="font-mono">Enabled</span></div>
          </div>
        </div>
      </div>

      <div className="flex justify-end">
        <button onClick={handleTrain} disabled={training}
          className="flex items-center gap-2 bg-accent/10 hover:bg-accent/20 text-accent border border-accent/30 px-4 py-2 rounded-lg text-sm transition-colors disabled:opacity-50">
          {training ? <Loader2 className="animate-spin" size={14}/> : <Play size={14}/>} Retrain Models
        </button>
      </div>
    </div>
  );
}
""")

print('ModelLab page done')
import logging, numpy as np, pandas as pd, joblib
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
logger = logging.getLogger(__name__)

class RegimeClusterer:
    def __init__(self, n_clusters=3):
        self.n_clusters = n_clusters
        self.scaler = StandardScaler()
        self.kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        self.label_map = {}
        self.fitted = False

    def _feats(self, df):
        feats = pd.DataFrame(index=df.index)
        ret = df.get('daily_return', df['Close'].pct_change())
        feats['rr20'] = ret.rolling(20).mean()
        feats['vol20'] = df.get('volatility_20d', ret.rolling(20).std() * np.sqrt(252))
        feats['trend'] = df.get('trend_slope_20', df['Close'].rolling(20).apply(lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x)==20 else np.nan, raw=False))
        sma50 = df.get('sma_50', df['Close'].rolling(50).mean())
        feats['dist'] = (df['Close'] - sma50) / sma50
        return feats.dropna()

    def fit(self, train_df):
        feats = self._feats(train_df)
        X = self.scaler.fit_transform(feats.values)
        self.kmeans.fit(X)
        centroids = self.scaler.inverse_transform(self.kmeans.cluster_centers_)
        lm = {}
        used = set()
        order = sorted(range(self.n_clusters), key=lambda i: centroids[i][0], reverse=True)
        labels = ['BULL', 'BEAR', 'SIDEWAYS']
        for rank, i in enumerate(order):
            r, v, t, d = centroids[i]
            if r > 0 and t > 0 and 'BULL' not in used:
                lm[i] = 'BULL'; used.add('BULL')
            elif (r < 0 or t < 0) and 'BEAR' not in used:
                lm[i] = 'BEAR'; used.add('BEAR')
            else:
                for lb in labels:
                    if lb not in used:
                        lm[i] = lb; used.add(lb); break
        self.label_map = lm
        self.fitted = True
        logger.info(f'Regime clustering fitted: {self.label_map}')

    def predict(self, df):
        if not self.fitted: raise RuntimeError('Not fitted')
        df = df.copy()
        feats = self._feats(df)
        X = self.scaler.transform(feats.values)
        clusters = self.kmeans.predict(X)
        rmap = {'BULL': 0, 'BEAR': 1, 'SIDEWAYS': 2}
        rs = pd.Series(2, index=df.index)
        rl = pd.Series('SIDEWAYS', index=df.index)
        for fi, cl in zip(feats.index, clusters):
            lb = self.label_map.get(cl, 'SIDEWAYS')
            rs[fi] = rmap[lb]; rl[fi] = lb
        df['regime_cluster'] = rs
        df['regime_cluster_label'] = rl
        return df

    def save(self, path):
        joblib.dump({'s': self.scaler, 'k': self.kmeans, 'l': self.label_map, 'n': self.n_clusters}, path)

    @classmethod
    def load(cls, path):
        d = joblib.load(path)
        o = cls(d['n']); o.scaler = d['s']; o.kmeans = d['k']; o.label_map = d['l']; o.fitted = True
        return o

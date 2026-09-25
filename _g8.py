import os
B = r'D:\PROJECTS\trademind\backend'
def w(p, c):
    fp = os.path.join(B, p)
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    with open(fp, 'w', encoding='utf-8') as f: f.write(c)
    print(f'  {p}')

w('app/storage/database.py', """import sqlite3, os, logging, json
from datetime import datetime
from app.core.config import settings

logger = logging.getLogger(__name__)
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'trademind.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS training_runs (
        id TEXT PRIMARY KEY, symbol TEXT, created_at TEXT,
        data_start TEXT, data_end TEXT,
        train_start TEXT, train_end TEXT,
        val_start TEXT, val_end TEXT,
        test_start TEXT, test_end TEXT,
        horizon INTEGER, threshold REAL,
        feature_count INTEGER, best_model TEXT,
        status TEXT, config_json TEXT, metrics_json TEXT,
        run_dir TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id TEXT, symbol TEXT, date TEXT,
        signal INTEGER, confidence REAL,
        prob_buy REAL, prob_hold REAL, prob_sell REAL,
        regime TEXT, regime_score REAL,
        model_name TEXT, features_json TEXT,
        FOREIGN KEY(run_id) REFERENCES training_runs(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS backtests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id TEXT, symbol TEXT, created_at TEXT,
        initial_capital REAL, transaction_cost REAL, slippage REAL,
        position_mode TEXT, metrics_json TEXT, equity_json TEXT,
        FOREIGN KEY(run_id) REFERENCES training_runs(id))''')
    conn.commit()
    conn.close()
    logger.info('Database initialized')

def save_training_run(run_data):
    conn = get_db()
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO training_runs
        (id, symbol, created_at, data_start, data_end,
         train_start, train_end, val_start, val_end,
         test_start, test_end, horizon, threshold,
         feature_count, best_model, status, config_json, metrics_json, run_dir)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
        (run_data['run_id'], run_data.get('symbol',''), datetime.now().isoformat(),
         run_data.get('data_start',''), run_data.get('data_end',''),
         run_data.get('train_start',''), run_data.get('train_end',''),
         run_data.get('val_start',''), run_data.get('val_end',''),
         run_data.get('test_start',''), run_data.get('test_end',''),
         run_data.get('horizon',5), run_data.get('threshold',0.01),
         run_data.get('feature_count',0), run_data.get('best_model',''),
         run_data.get('status','completed'),
         json.dumps(run_data.get('config',{})),
         json.dumps(run_data.get('metrics',{}), default=str),
         run_data.get('run_dir','')))
    conn.commit()
    conn.close()

def get_latest_run(symbol):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM training_runs WHERE symbol=? ORDER BY created_at DESC LIMIT 1', (symbol,))
    row = c.fetchone()
    conn.close()
    if row: return dict(row)
    return None

def save_predictions(predictions):
    conn = get_db()
    c = conn.cursor()
    for p in predictions:
        c.execute('''INSERT INTO predictions
            (run_id, symbol, date, signal, confidence,
             prob_buy, prob_hold, prob_sell, regime, regime_score, model_name, features_json)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''',
            (p.get('run_id',''), p.get('symbol',''), p.get('date',''),
             p.get('signal',1), p.get('confidence',0),
             p.get('prob_buy',0), p.get('prob_hold',0), p.get('prob_sell',0),
             p.get('regime',''), p.get('regime_score',0),
             p.get('model_name',''), json.dumps(p.get('features',[]))))
    conn.commit()
    conn.close()

def get_predictions(symbol, limit=100):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM predictions WHERE symbol=? ORDER BY date DESC LIMIT ?', (symbol, limit))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def save_backtest(bt_data):
    conn = get_db()
    c = conn.cursor()
    c.execute('''INSERT INTO backtests
        (run_id, symbol, created_at, initial_capital, transaction_cost,
         slippage, position_mode, metrics_json, equity_json)
        VALUES (?,?,?,?,?,?,?,?,?)''',
        (bt_data.get('run_id',''), bt_data.get('symbol',''), datetime.now().isoformat(),
         bt_data.get('initial_capital',100000), bt_data.get('transaction_cost',0.001),
         bt_data.get('slippage',0.0005), bt_data.get('position_mode','long_short'),
         json.dumps(bt_data.get('metrics',{}), default=str),
         json.dumps(bt_data.get('equity_curve',[]), default=str)))
    conn.commit()
    conn.close()

def get_latest_backtest(symbol):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM backtests WHERE symbol=? ORDER BY created_at DESC LIMIT 1', (symbol,))
    row = c.fetchone()
    conn.close()
    if row: return dict(row)
    return None

init_db()
""")

print('Storage done')
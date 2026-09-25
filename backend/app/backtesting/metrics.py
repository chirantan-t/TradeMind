import numpy as np

def calculate_metrics(equity_curve, trades, initial_capital=100000.0,
                      total_costs=0.0, total_slippage=0.0):
    if not equity_curve or len(equity_curve) < 2:
        return {'error': 'Insufficient data'}
    sv = np.array([e['strategy'] for e in equity_curve])
    bv = np.array([e['benchmark'] for e in equity_curve])
    dd = np.array([e['drawdown'] for e in equity_curve])
    n = len(sv)
    sdr = np.diff(sv) / sv[:-1]
    cum_ret = (sv[-1] / initial_capital) - 1
    bench_ret = (bv[-1] / initial_capital) - 1
    years = n / 252
    ann_ret = (1 + cum_ret)**(1/max(years, 0.01)) - 1 if cum_ret > -1 else -1
    vol = float(np.std(sdr) * np.sqrt(252)) if len(sdr) > 0 else 0
    sharpe = float(np.mean(sdr) / np.std(sdr) * np.sqrt(252)) if np.std(sdr) > 0 else 0
    max_dd = float(np.min(dd)) if len(dd) > 0 else 0
    win_days = np.sum(sdr > 0)
    win_rate = float(win_days / len(sdr)) if len(sdr) > 0 else 0
    n_trades = len(trades)
    alpha = cum_ret - bench_ret
    return {
        'cumulative_return': float(cum_ret), 'annualized_return': float(ann_ret),
        'benchmark_return': float(bench_ret), 'sharpe_ratio': float(sharpe),
        'max_drawdown': float(max_dd), 'volatility': float(vol),
        'win_rate': float(win_rate), 'total_trades': n_trades,
        'alpha': float(alpha), 'total_transaction_costs': float(total_costs),
        'total_slippage': float(total_slippage),
        'net_pnl': float(sv[-1] - initial_capital),
        'final_equity': float(sv[-1]),
        'period_start': equity_curve[0]['date'],
        'period_end': equity_curve[-1]['date'],
        'trading_days': n}

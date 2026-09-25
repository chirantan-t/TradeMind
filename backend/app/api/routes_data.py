from fastapi import APIRouter, HTTPException
from app.core.config import settings
from app.data.loader import load_data
from app.core.pipeline import get_cache, load_cached_model

router = APIRouter(prefix='/api', tags=['data'])

@router.get('/health')
def health():
    return {'status': 'ok', 'service': 'TradeMind API'}

@router.get('/assets')
def get_assets():
    return {'assets': [
        {'symbol': s, 'name': settings.ASSET_NAMES.get(s, s),
         'currency': settings.ASSET_CURRENCIES.get(s, 'USD')}
        for s in settings.SUPPORTED_ASSETS]}

@router.get('/fundamentals/{symbol}')
def get_fundamentals(symbol: str):
    from app.data.provider import market_provider
    try:
        fundamentals = market_provider.get_current_fundamentals(symbol)
        return {'symbol': symbol, 'fundamentals': fundamentals}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/dataset/{symbol}/summary')
def dataset_summary(symbol: str):
    cache = get_cache(symbol) or load_cached_model(symbol)
    if cache:
        q = cache['quality']
        m = cache['meta']
        si = cache.get('split_info', {})
        ti = cache.get('target_info', {})
        return {
            'source': m.get('source', 'Yahoo Finance'),
            'symbol': symbol, 'name': settings.ASSET_NAMES.get(symbol, symbol),
            'start': m.get('start', ''), 'end': m.get('end', ''),
            'rows': q.total_rows if hasattr(q, 'total_rows') else m.get('rows', 0),
            'missing_values': q.missing_values if hasattr(q, 'missing_values') else 0,
            'duplicate_dates': q.duplicate_dates if hasattr(q, 'duplicate_dates') else 0,
            'invalid_ohlc': q.invalid_ohlc_rows if hasattr(q, 'invalid_ohlc_rows') else 0,
            'feature_count': len(cache.get('feature_cols', [])),
            'split_info': si, 'target_info': ti,
            'class_distribution': ti.get('class_distribution', {}),
            'regime_distribution': cache.get('regime_dist', {}),
            'currency': settings.ASSET_CURRENCIES.get(symbol, 'USD'),
        }
    # Try loading without training
    try:
        df, meta, quality = load_data(symbol)
        return {
            'source': meta['source'], 'symbol': symbol,
            'name': settings.ASSET_NAMES.get(symbol, symbol),
            'start': meta['start'], 'end': meta['end'],
            'rows': quality.total_rows, 'missing_values': quality.missing_values,
            'duplicate_dates': quality.duplicate_dates,
            'invalid_ohlc': quality.invalid_ohlc_rows,
            'feature_count': 0, 'split_info': {},
            'target_info': {}, 'class_distribution': {},
            'regime_distribution': {},
            'currency': settings.ASSET_CURRENCIES.get(symbol, 'USD'),
            'status': 'data_only',
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Unable to retrieve data: {str(e)}')

@router.get('/dataset/{symbol}/prices')
def dataset_prices(symbol: str, limit: int = 500):
    cache = get_cache(symbol) or load_cached_model(symbol)
    if cache and cache.get('df') is not None:
        df = cache['df']
    else:
        try:
            df, _, _ = load_data(symbol)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    df_out = df.tail(limit)
    records = []
    for _, row in df_out.iterrows():
        r = {'date': row['Date'].strftime('%Y-%m-%d'), 'open': float(row['Open']),
             'high': float(row['High']), 'low': float(row['Low']),
             'close': float(row['Close']), 'volume': float(row['Volume'])}
        if 'regime_label' in row.index:
            r['regime'] = row['regime_label']
        records.append(r)
    return {'symbol': symbol, 'prices': records}

@router.post('/data/refresh')
def refresh_data(symbol: str = '^NSEI'):
    try:
        df, meta, quality = load_data(symbol, force_download=True)
        return {'status': 'refreshed', 'symbol': symbol,
                'rows': quality.total_rows, 'start': meta['start'], 'end': meta['end']}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

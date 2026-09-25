import sys
import logging
from app.data.downloader import download_ohlcv
from app.data.loader import load_data
from app.features.builder import build_features
from app.features.target import generate_target
from app.data.splitter import chronological_split
from app.models.trainer import train_all_models

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_test():
    symbol = '^NSEI'
    logger.info("1. Downloading data...")
    res = download_ohlcv(symbol, start='2020-01-01')
    
    logger.info("2. Loading data...")
    df, meta, report = load_data(symbol)
    
    logger.info("3. Feature engineering...")
    df_feat, feature_cols = build_features(df)
    
    logger.info("4. Target generation...")
    df_tgt, info = generate_target(df_feat)
    
    logger.info("5. Data splitting...")
    train_df, val_df, test_df, split_info = chronological_split(df_tgt)
    
    logger.info("6. Model training...")
    res = train_all_models(train_df, val_df, test_df, feature_cols, symbol=symbol)
    
    logger.info("Pipeline successful!")
    logger.info(f"Best model: {res['best_model']} with F1: {res['best_val_f1']}")

if __name__ == '__main__':
    run_test()

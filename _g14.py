import os
B = r'D:\PROJECTS\trademind\backend'
def w(p, c):
    fp = os.path.join(B, p)
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    with open(fp, 'w', encoding='utf-8') as f: f.write(c)
    print(f'  {p}')

w('app/main.py', """import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes_data import router as data_router
from app.api.routes_training import router as training_router
from app.api.routes_predictions import router as predictions_router
from app.api.routes_models import router as models_router
from app.api.routes_backtest import router as backtest_router

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(
    title='TradeMind API',
    description='Market Regime Detection and Explainable Trading-Signal Generation',
    version='1.0.0',
)

origins = [o.strip() for o in settings.CORS_ORIGINS.split(',')]
app.add_middleware(
    CORSMiddleware, allow_origins=origins + ['*'],
    allow_credentials=True, allow_methods=['*'], allow_headers=['*'])

app.include_router(data_router)
app.include_router(training_router)
app.include_router(predictions_router)
app.include_router(models_router)
app.include_router(backtest_router)

@app.on_event('startup')
async def startup():
    from app.storage.database import init_db
    init_db()
    logger.info('TradeMind API started')
""")

print('main.py done')
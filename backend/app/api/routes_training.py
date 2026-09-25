import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.schemas.training import TrainRequest
from app.core.pipeline import run_training_pipeline

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/api', tags=['training'])

# Track training status
_training_status = {}

@router.post('/train')
def train_models(req: TrainRequest):
    try:
        result = run_training_pipeline(
            symbol=req.symbol, horizon=req.horizon,
            threshold=req.threshold, train_ratio=req.train_ratio,
            val_ratio=req.validation_ratio, use_regime=req.use_regime)
        return result
    except Exception as e:
        logger.error(f'Training failed: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail=f'Training failed: {str(e)}')

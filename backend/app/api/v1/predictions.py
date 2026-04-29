from fastapi import APIRouter

router = APIRouter(
    prefix="/api/v1/predictions",
    tags=["Predictions"]
)

@router.get("/{symbol}")
def predict_stock(symbol: str):
    return {
        "symbol": symbol.upper(),
        "prediction": "RISE",
        "confidence": 0.78,
        "risk_level": "MEDIUM"
    }

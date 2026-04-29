from fastapi import APIRouter

router = APIRouter(
    prefix="/api/v1/demo",
    tags=["Demo"]
)

@router.get("/stocks")
def get_demo_stocks():
    return {
        "stocks": [
            {"symbol": "AAPL", "name": "Apple Inc.", "sector": "Technology"},
            {"symbol": "GOOGL", "name": "Alphabet Inc.", "sector": "Technology"},
            {"symbol": "MSFT", "name": "Microsoft Corporation", "sector": "Technology"},
            {"symbol": "AMZN", "name": "Amazon", "sector": "E-Commerce"},
        ]
    }

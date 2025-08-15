from fastapi import APIRouter
from fastapi.responses import JSONResponse
from src.db.queries import get_all_spots

router = APIRouter(prefix="/spots", tags=["spots"])

@router.get("")
async def get_all_spots_endpoint():
    """
    Endpoint para retornar uma lista de todos os spots disponíveis.
    """
    try:
        spots_raw = await get_all_spots()
        if spots_raw:
            return spots_raw
        else:
            return JSONResponse(status_code=404, content={"message": "Nenhum spot encontrado."})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Erro ao buscar spots: {e}"})
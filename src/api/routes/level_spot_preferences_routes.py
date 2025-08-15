from fastapi import APIRouter, HTTPException, Query
from src.db.queries import get_user_surf_level, get_level_spot_preferences

router = APIRouter(prefix="/level-spot-preferences", tags=["level-spot-preferences"])

@router.get("/{spot_id}")
async def get_level_spot_preferences_endpoint(spot_id: int, user_id: str = Query(...)):
    """
    Endpoint para obter as preferências de spot padrão com base no nível de surf do usuário.
    """
    surf_level = await get_user_surf_level(user_id)
    if not surf_level:
        raise HTTPException(status_code=404, detail=f"Nível de surf não encontrado para o usuário com ID {user_id}.")

    preferences = await get_level_spot_preferences(surf_level, spot_id)
    if not preferences:
        raise HTTPException(status_code=404, detail=f"Nenhuma preferência padrão encontrada para o nível de surf '{surf_level}' no spot ID {spot_id}.")

    return preferences
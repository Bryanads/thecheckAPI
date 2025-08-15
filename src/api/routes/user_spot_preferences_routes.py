# src/api/routes/user_spot_preferences_routes.py
from fastapi import APIRouter, HTTPException, Body
from src.db.queries import get_spot_preferences, set_user_spot_preferences, toggle_spot_preference_active

router = APIRouter(prefix="/user-spot-preferences", tags=["user-spot-preferences"])

@router.get("/{user_id}/{spot_id}")
async def get_user_spot_preferences_endpoint(user_id: str, spot_id: int):
    preferences = await get_spot_preferences(user_id, spot_id, preference_type='user')
    if not preferences:
        raise HTTPException(status_code=404, detail="Preferências do usuário não encontradas para este spot.")
    return preferences

@router.post("/{user_id}/{spot_id}")
async def set_user_spot_preferences_endpoint(user_id: str, spot_id: int, preferences: dict):
    try:
        await set_user_spot_preferences(user_id, spot_id, preferences)
        return {"message": "Preferências salvas com sucesso."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{user_id}/{spot_id}/toggle")
async def toggle_spot_preference_active_endpoint(user_id: str, spot_id: int, is_active: bool = Body(..., embed=True)):
    try:
        await toggle_spot_preference_active(user_id, spot_id, is_active)
        return {"message": f"Status de ativação da preferência definido como {is_active}."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
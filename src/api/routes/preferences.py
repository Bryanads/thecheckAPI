from fastapi import APIRouter, Depends, HTTPException, status
from src.core.schemas import Preference, PreferenceUpdate
from src.db import queries
from src.api.dependencies.auth import get_current_user_id

router = APIRouter(
    prefix="/preferences",
    tags=["Preferences"]
)

@router.get("/spot/{spot_id}", response_model=Preference)
async def get_spot_preferences(
    spot_id: int,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Retorna as preferências do usuário para um pico específico.
    Se não houver preferências customizadas, retorna um padrão com base no nível de surf.
    """
    preferences = await queries.get_preferences_by_user_and_spot(current_user_id, spot_id)
    
    if not preferences:
        # Busca o perfil do usuário para saber seu nível de surf
        user_profile = await queries.get_profile_by_id(current_user_id)
        if not user_profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found.")
        
        surf_level = user_profile.get('surf_level', 'intermediario')
        default_prefs = await queries.get_default_preferences_by_level(surf_level)
        
        # Simula uma resposta da tabela para corresponder ao schema, mas sem salvar
        return {
            "preference_id": 0, "user_id": current_user_id, "spot_id": spot_id, 
            "is_active": True, **default_prefs
        }
        
    return preferences

@router.put("/spot/{spot_id}", response_model=Preference)
async def set_spot_preferences(
    spot_id: int,
    preference_update: PreferenceUpdate,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Cria ou atualiza as preferências do usuário para um pico específico.
    """
    update_data = preference_update.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update data provided.")
    
    updated_preferences = await queries.create_or_update_preferences(current_user_id, spot_id, update_data)
    
    return updated_preferences
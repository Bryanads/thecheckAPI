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
    Retorna as preferências para um pico, seguindo a hierarquia:
    1. Preferências customizadas e ativas do usuário.
    2. Preferências padrão do pico para o nível do usuário.
    3. Preferências genéricas para o nível do usuário (fallback).
    """
    # Nível 1: Tenta buscar as preferências customizadas do usuário
    user_prefs = await queries.get_user_spot_preferences(current_user_id, spot_id)
    if user_prefs:
        return user_prefs

    # Se não houver, busca o perfil para obter o nível de surf
    user_profile = await queries.get_profile_by_id(current_user_id)
    if not user_profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found.")
    surf_level = user_profile.get('surf_level', 'intermediario')

    # Nível 2: Tenta buscar as preferências padrão do spot para o nível do usuário
    spot_level_prefs = await queries.get_spot_level_preferences(spot_id, surf_level)
    if spot_level_prefs:
        # Simula uma resposta completa para corresponder ao schema
        return {**spot_level_prefs, "user_id": current_user_id, "is_active": False}

    # Nível 3 (Fallback): Retorna as preferências genéricas para o nível
    generic_prefs = await queries.get_generic_preferences_by_level(surf_level)
    return {
        "preference_id": 0, "user_id": current_user_id, "spot_id": spot_id, 
        "is_active": False, **generic_prefs
    }

@router.put("/spot/{spot_id}", response_model=Preference)
async def set_spot_preferences(
    spot_id: int,
    preference_update: PreferenceUpdate,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Cria ou atualiza as preferências customizadas do usuário para um pico específico.
    """
    update_data = preference_update.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update data provided.")
    
    # Esta função agora se refere apenas às preferências do usuário
    updated_preferences = await queries.create_or_update_user_preferences(current_user_id, spot_id, update_data)
    
    return updated_preferences
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional
from src.core.schemas import Profile, ProfileUpdate
from src.db import queries
from src.api.dependencies.auth import get_current_user_id

router = APIRouter(
    prefix="/profile",
    tags=["Profile"]
)

@router.get("/", response_model=Profile)
async def get_current_user_profile(
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Retorna o perfil do usuário atualmente autenticado.
    """
    profile = await queries.get_profile_by_id(current_user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found for the authenticated user."
        )
    return profile


@router.put("/", response_model=Profile)
async def update_current_user_profile(
    profile_update: ProfileUpdate,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Atualiza o perfil do usuário atualmente autenticado.
    """
    # .model_dump(exclude_unset=True) garante que só enviaremos para a query
    # os campos que o usuário realmente enviou na requisição.
    update_data = profile_update.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No update data provided."
        )

    updated_profile = await queries.update_profile(current_user_id, update_data)

    if not updated_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found for the authenticated user."
        )
    
    return updated_profile
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from src.db.queries import (
    get_user_by_id,
    update_user_profile
)

router = APIRouter(prefix="/users", tags=["users"])

class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None
    surf_level: Optional[str] = None
    goofy_regular_stance: Optional[str] = None
    preferred_wave_direction: Optional[str] = None
    bio: Optional[str] = None
    profile_picture_url: Optional[str] = None

@router.get("/profile/{user_id}")
async def get_user_profile(user_id: str):
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # A verificação acima garante que 'user' não é None aqui.
    user_data = {k: v for k, v in user.items() if k != 'password_hash'}
    return user_data

@router.put("/profile/{user_id}")
async def update_user_profile_endpoint(user_id: str, request: UpdateProfileRequest):
    update_fields = {k: v for k, v in request.dict().items() if v is not None}
    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    try:
        await update_user_profile(user_id, update_fields)
        updated_user = await get_user_by_id(user_id)
        
        # --- CORREÇÃO ADICIONADA AQUI ---
        # Verifica se o usuário foi encontrado APÓS a atualização.
        if not updated_user:
            raise HTTPException(status_code=404, detail="Updated user could not be found.")

        # Se a verificação passar, o código continua com segurança.
        user_data = {k: v for k, v in updated_user.items() if k != 'password_hash'}
        return {"message": "Profile updated successfully", "user": user_data}
        
    except Exception as e:
        # Retorna o detalhe do erro para facilitar a depuração no frontend.
        raise HTTPException(status_code=500, detail=f"Failed to update profile: {str(e)}")
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from src.core.schemas import Preset, PresetCreate, PresetUpdate
from src.db import queries
from src.api.dependencies.auth import get_current_user_id

router = APIRouter(
    prefix="/presets",
    tags=["Presets"]
)

@router.post("/", response_model=Preset, status_code=status.HTTP_201_CREATED)
async def create_new_preset(
    preset: PresetCreate,
    current_user_id: str = Depends(get_current_user_id)
):
    """Cria um novo preset para o usuário autenticado."""
    new_preset = await queries.create_preset(current_user_id, preset.model_dump())
    return new_preset

@router.get("/", response_model=List[Preset])
async def get_user_presets(
    current_user_id: str = Depends(get_current_user_id)
):
    """Retorna todos os presets do usuário autenticado."""
    return await queries.get_presets_by_user_id(current_user_id)

@router.put("/{preset_id}", response_model=Preset)
async def update_existing_preset(
    preset_id: int,
    preset_update: PresetUpdate,
    current_user_id: str = Depends(get_current_user_id)
):
    """Atualiza um preset existente do usuário."""
    update_data = preset_update.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No update data provided.")
    
    updated_preset = await queries.update_preset(current_user_id, preset_id, update_data)
    if not updated_preset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Preset not found.")
    return updated_preset

@router.delete("/{preset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_preset(
    preset_id: int,
    current_user_id: str = Depends(get_current_user_id)
):
    """Deleta um preset existente do usuário."""
    success = await queries.delete_preset(current_user_id, preset_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Preset not found.")
    return None 
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import datetime
from src.db.queries import (
    create_user_recommendation_preset,
    get_user_recommendation_presets,
    get_user_recommendation_preset_by_id,
    update_user_recommendation_preset,
    delete_user_recommendation_preset,
    get_user_by_id,
    get_default_user_recommendation_preset
)

router = APIRouter(prefix="/presets", tags=["presets"])

class PresetCreateRequest(BaseModel):
    user_id: str
    preset_name: str
    spot_ids: list[int]
    start_time: str
    end_time: str
    weekdays: list[int] | None = None 
    is_default: bool = False

class PresetUpdateRequest(BaseModel):
    user_id: str
    preset_name: str | None = None
    spot_ids: list[int] | None = None
    start_time: str | None = None
    end_time: str | None = None
    weekdays: list[int] | None = None
    is_default: bool | None = None
    is_active: bool | None = None

@router.post("")
async def create_preset_endpoint(request: PresetCreateRequest):
    data = request.dict()
    user_id = data.get('user_id')
    preset_name = data.get('preset_name')
    spot_ids = data.get('spot_ids')
    start_time_str = data.get('start_time')
    end_time_str = data.get('end_time')
    weekdays = data.get('weekdays') 
    is_default = data.get('is_default', False)

    if not all([user_id, preset_name, spot_ids, start_time_str, end_time_str]):
        raise HTTPException(status_code=400, detail="Todos os campos obrigatórios (user_id, preset_name, spot_ids, start_time, end_time) são necessários.")

    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"Usuário com ID {user_id} não encontrado.")

    try:
        spot_ids = [int(s_id) for s_id in spot_ids]
        start_time = datetime.time.fromisoformat(start_time_str)
        end_time = datetime.time.fromisoformat(end_time_str)
        if weekdays is not None:
            if not isinstance(weekdays, list) or not all(isinstance(d, int) and 0 <= d <= 6 for d in weekdays):
                raise HTTPException(status_code=400, detail="weekdays deve ser uma lista de inteiros entre 0 (Domingo) e 6 (Sábado).")
    except (ValueError, TypeError) as e:
        raise HTTPException(status_code=400, detail=f"Erro de formato de dados: {e}")

    try:
        preset_id = await create_user_recommendation_preset(
            user_id, preset_name, spot_ids, start_time, end_time, weekdays, is_default
        )
        return {"message": "Preset criado com sucesso!", "preset_id": preset_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falha ao criar preset: {e}")

@router.get("")
async def get_presets_endpoint(user_id: str = Query(...)):
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"Usuário com ID {user_id} não encontrado.")
    try:
        presets = await get_user_recommendation_presets(user_id)
        for preset in presets:
            if isinstance(preset.get('start_time'), datetime.time):
                preset['start_time'] = preset['start_time'].strftime('%H:%M:%S')
            if isinstance(preset.get('end_time'), datetime.time):
                preset['end_time'] = preset['end_time'].strftime('%H:%M:%S')
        return presets
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falha ao buscar presets: {e}")
    if not user:
        return jsonify({"error": f"Usuário com ID {user_id} não encontrado."}), 404

    try:
        presets = get_user_recommendation_presets(user_id)
        for preset in presets:
            if isinstance(preset.get('start_time'), datetime.time):
                preset['start_time'] = preset['start_time'].strftime('%H:%M:%S')
            if isinstance(preset.get('end_time'), datetime.time):
                preset['end_time'] = preset['end_time'].strftime('%H:%M:%S')
        return jsonify(presets), 200
    except Exception as e:
        return jsonify({"error": f"Falha ao buscar presets: {e}"}), 500


# GET preset by id
@router.get("/{preset_id}")
async def get_preset_by_id_endpoint(preset_id: int, user_id: str = Query(...)):
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"Usuário com ID {user_id} não encontrado.")
    try:
        preset = await get_user_recommendation_preset_by_id(preset_id, user_id)
        if not preset:
            raise HTTPException(status_code=404, detail=f"Preset com ID {preset_id} não encontrado para o usuário {user_id}.")
        if isinstance(preset.get('start_time'), datetime.time):
            preset['start_time'] = preset['start_time'].strftime('%H:%M:%S')
        if isinstance(preset.get('end_time'), datetime.time):
            preset['end_time'] = preset['end_time'].strftime('%H:%M:%S')
        return preset
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falha ao buscar preset: {e}")

# PUT update preset
@router.put("/{preset_id}")
async def update_preset_endpoint(preset_id: int, request: PresetUpdateRequest):
    # Usamos .model_dump() com exclude_unset=True para pegar apenas os campos enviados na requisição
    data = request.model_dump(exclude_unset=True)
    user_id = data.get('user_id')

    if not user_id:
        raise HTTPException(status_code=400, detail="Campo 'user_id' é obrigatório no corpo da requisição.")

    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"Usuário com ID {user_id} não encontrado.")

    updates = {}

    # Mantém a lógica para os campos que não precisam de conversão
    if 'preset_name' in data:
        updates['preset_name'] = data['preset_name']
    if 'is_default' in data:
        updates['is_default'] = bool(data['is_default'])
    if 'is_active' in data:
        updates['is_active'] = bool(data['is_active'])

    # Lógica de conversão para campos específicos
    if 'spot_ids' in data:
        try:
            updates['spot_ids'] = [int(s_id) for s_id in data['spot_ids']]
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="spot_ids deve ser uma lista de IDs de spots inteiros.")

    if 'weekdays' in data:
        try:
            if not isinstance(data['weekdays'], list):
                raise HTTPException(status_code=400, detail="weekdays deve ser uma lista de números inteiros.")
            updates['weekdays'] = [int(offset) for offset in data['weekdays']]
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="weekdays deve ser uma lista de números inteiros.")

    # CORREÇÃO: Checar o dicionário 'data' original e usar o formato de tempo correto
    if 'start_time' in data:
        try:
            # CORREÇÃO: Usar o formato HH:MM:SS
            updates['start_time'] = datetime.time.fromisoformat(data['start_time'])
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="Formato de start_time inválido. Use HH:MM:SS.")

    if 'end_time' in data:
        try:
            # CORREÇÃO: Usar o formato HH:MM:SS
            updates['end_time'] = datetime.time.fromisoformat(data['end_time'])
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="Formato de end_time inválido. Use HH:MM:SS.")

    if not updates:
        raise HTTPException(status_code=400, detail="Nenhum campo fornecido para atualização.")

    try:
        success = await update_user_recommendation_preset(preset_id, user_id, updates)
        if success:
            return {"message": "Preset atualizado com sucesso!"}
        else:
            raise HTTPException(status_code=404, detail="Preset não encontrado ou não autorizado para atualização.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falha ao atualizar preset: {e}")

# DELETE preset
@router.delete("/{preset_id}")
async def delete_preset_endpoint(preset_id: int, user_id: str = Query(...)):
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"Usuário com ID {user_id} não encontrado.")
    try:
        success = await delete_user_recommendation_preset(preset_id, user_id)
        if success:
            return {"message": "Preset desativado (excluído logicamente) com sucesso!"}
        else:
            raise HTTPException(status_code=404, detail="Preset não encontrado ou não autorizado para desativação.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falha ao desativar preset: {e}")

# GET default preset
@router.get("/default")
async def get_default_preset_endpoint(user_id: str = Query(...)):
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"Usuário com ID {user_id} não encontrado.")
    try:
        preset = await get_default_user_recommendation_preset(user_id)
        if not preset:
            return {"message": "Nenhum preset padrão encontrado para este usuário."}
        if isinstance(preset.get('start_time'), datetime.time):
            preset['start_time'] = preset['start_time'].strftime('%H:%M:%S')
        if isinstance(preset.get('end_time'), datetime.time):
            preset['end_time'] = preset['end_time'].strftime('%H:%M:%S')
        return preset
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falha ao buscar preset padrão: {e}")
from src.db.connection import get_connection, release_connection
from typing import List, Dict, Any, Optional
import datetime

async def get_all_spots() -> List[Dict[str, Any]]:
    """
    Busca todos os spots de surf do banco de dados.
    """
    conn = await get_connection()
    try:
        # A query SQL para selecionar todos os campos de todos os spots
        rows = await conn.fetch("SELECT * FROM spots ORDER BY name;")
        # Converte o resultado (lista de Records) para uma lista de dicionários
        return [dict(row) for row in rows]
    finally:
        # Libera a conexão de volta para o pool
        await conn.close() # Em versões mais recentes do asyncpg, close() retorna ao pool

async def get_spot_by_id(spot_id: int) -> Optional[Dict[str, Any]]:
    """
    Busca os detalhes de um único spot pelo seu ID.
    """
    conn = await get_connection()
    try:
        row = await conn.fetchrow("SELECT * FROM spots WHERE spot_id = $1", spot_id)
        return dict(row) if row else None
    finally:
        await conn.close()

async def get_profile_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Busca um perfil de usuário pelo seu ID (UUID).
    """
    conn = await get_connection()
    try:
        row = await conn.fetchrow("SELECT * FROM profiles WHERE id = $1", user_id)
        if row:
            profile_dict = dict(row)
            # Explicitly convert the UUID to a string to match the schema
            profile_dict['id'] = str(profile_dict['id'])
            return profile_dict
        return None
    finally:
        await conn.close()

async def update_profile(user_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Atualiza o perfil de um usuário com base nos dados fornecidos.
    """
    if not updates:
        return None

    conn = await get_connection()
    try:
        # Constrói a query SQL dinamicamente
        set_parts = [f"{key} = ${i + 2}" for i, key in enumerate(updates.keys())]
        set_parts.append("updated_at = NOW()")
        set_clause = ", ".join(set_parts)
        
        query = f"UPDATE profiles SET {set_clause} WHERE id = $1 RETURNING *;"
        
        values = [user_id] + list(updates.values())

        updated_row = await conn.fetchrow(query, *values)
        
        if updated_row:
            updated_profile = dict(updated_row)
            updated_profile['id'] = str(updated_profile['id'])
            return updated_profile
        return None
    finally:
        await conn.close()

async def create_preset(user_id: str, preset_data: Dict[str, Any]) -> Dict[str, Any]:
    """Cria um novo preset para um usuário."""
    conn = await get_connection()
    try:
        # Se o novo preset for default, desmarca qualquer outro preset default do usuário
        if preset_data.get('is_default'):
            await conn.execute("UPDATE presets SET is_default = FALSE WHERE user_id = $1", user_id)

        # Insere o novo preset
        row = await conn.fetchrow(
            """
            INSERT INTO presets (user_id, name, spot_ids, start_time, end_time, day_selection_type, day_selection_values, is_default)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING *;
            """,
            user_id,
            preset_data['name'],
            preset_data['spot_ids'],
            preset_data['start_time'],
            preset_data['end_time'],
            preset_data['day_selection_type'],
            preset_data['day_selection_values'],
            preset_data['is_default']
        )
        new_preset = dict(row)
        new_preset['user_id'] = str(new_preset['user_id'])
        return new_preset
    finally:
        await conn.close()

async def get_presets_by_user_id(user_id: str) -> List[Dict[str, Any]]:
    """Busca todos os presets de um usuário."""
    conn = await get_connection()
    try:
        rows = await conn.fetch("SELECT * FROM presets WHERE user_id = $1 ORDER BY name", user_id)
        
        # Converte cada linha para um dicionário e garante que o UUID seja uma string
        presets = [dict(row) for row in rows]
        for preset in presets:
            if 'user_id' in preset:
                preset['user_id'] = str(preset['user_id'])
        
        return presets
    finally:
        await conn.close()

async def update_preset(user_id: str, preset_id: int, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Atualiza um preset existente."""
    if not updates:
        return None
    conn = await get_connection()
    try:
        # Lógica para garantir que apenas um preset seja o default
        if updates.get('is_default'):
            await conn.execute("UPDATE presets SET is_default = FALSE WHERE user_id = $1 AND preset_id != $2", user_id, preset_id)

        set_clause = ", ".join(f"{key} = ${i + 3}" for i, key in enumerate(updates.keys()))
        query = f"UPDATE presets SET {set_clause} WHERE preset_id = $1 AND user_id = $2 RETURNING *;"
        values = [preset_id, user_id] + list(updates.values())
        
        updated_row = await conn.fetchrow(query, *values)
        if updated_row:
            updated_preset = dict(updated_row)
            # Converte o UUID para string para corresponder ao schema
            updated_preset['user_id'] = str(updated_preset['user_id'])
            return updated_preset
        return None
    finally:
        await conn.close()

async def delete_preset(user_id: str, preset_id: int) -> bool:
    """Deleta um preset de um usuário."""
    conn = await get_connection()
    try:
        result = await conn.execute("DELETE FROM presets WHERE preset_id = $1 AND user_id = $2", preset_id, user_id)
        # result retorna 'DELETE 1' em caso de sucesso
        return result.strip('DELETE ') == '1'
    finally:
        await conn.close()

async def get_preferences_by_user_and_spot(user_id: str, spot_id: int) -> Optional[Dict[str, Any]]:
    """Busca as preferências customizadas de um usuário para um spot específico."""
    conn = await get_connection()
    try:
        row = await conn.fetchrow(
            "SELECT * FROM user_spot_preferences WHERE user_id = $1 AND spot_id = $2",
            user_id, spot_id
        )
        if not row:
            return None
        
        preferences = dict(row)
        if 'user_id' in preferences and preferences['user_id'] is not None:
            preferences['user_id'] = str(preferences['user_id'])
            
        return preferences
    finally:
        await conn.close()

async def get_default_preferences_by_level(surf_level: str) -> Dict[str, Any]:
    """
    Retorna um conjunto de preferências padrão com base no nível de surf.
    Estes valores podem vir de uma tabela de 'level_preferences' no futuro.
    """
    if surf_level == 'iniciante':
        return {
            "ideal_swell_height": 1.0,
            "max_swell_height": 1.5,
            "max_wind_speed": 5.0,
            "ideal_water_temperature": 24.0,
            "ideal_air_temperature": 26.0,
        }
    # Padrão para intermediário/avançado
    return {
        "ideal_swell_height": 1.8,
        "max_swell_height": 2.8,
        "max_wind_speed": 8.0,
        "ideal_water_temperature": 22.0,
        "ideal_air_temperature": 25.0,
    }

async def create_or_update_preferences(user_id: str, spot_id: int, updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Cria ou atualiza (UPSERT) as preferências de um usuário para um spot.
    """
    conn = await get_connection()
    try:
        # Constrói a query de UPSERT
        set_clause = ", ".join(f"{key} = EXCLUDED.{key}" for key in updates.keys())
        
        query = f"""
        INSERT INTO user_spot_preferences (user_id, spot_id, {", ".join(updates.keys())})
        VALUES ($1, $2, {", ".join(f"${i + 3}" for i in range(len(updates)))})
        ON CONFLICT (user_id, spot_id) DO UPDATE SET {set_clause}
        RETURNING *;
        """
        values = [user_id, spot_id] + list(updates.values())
        
        row = await conn.fetchrow(query, *values)
        
        # AQUI A CORREÇÃO: Converte o UUID para string antes de retornar
        updated_preferences = dict(row)
        if 'user_id' in updated_preferences and updated_preferences['user_id'] is not None:
            updated_preferences['user_id'] = str(updated_preferences['user_id'])
        
        return updated_preferences
    finally:
        await conn.close()

async def get_forecasts_for_spot(spot_id: int, start_utc: datetime.datetime, end_utc: datetime.datetime) -> List[Dict[str, Any]]:
    """
    Busca os dados de previsão brutos para um spot em um intervalo de tempo.
    """
    conn = await get_connection()
    try:
        rows = await conn.fetch(
            """
            SELECT * FROM forecasts 
            WHERE spot_id = $1 AND timestamp_utc BETWEEN $2 AND $3
            ORDER BY timestamp_utc;
            """,
            spot_id, start_utc, end_utc
        )
        return [dict(row) for row in rows]
    finally:
        await conn.close()
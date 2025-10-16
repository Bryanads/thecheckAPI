from src.db.connection import get_connection, release_connection
from typing import List, Dict, Any, Optional
import datetime
import json

async def get_all_spots() -> List[Dict[str, Any]]:
    """
    Busca todos os spots de surf do banco de dados.
    """
    conn = await get_connection()
    try:
        rows = await conn.fetch("SELECT * FROM spots ORDER BY name;")
        return [dict(row) for row in rows]
    finally:
        await conn.close()

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
        if preset_data.get('is_default'):
            await conn.execute("UPDATE presets SET is_default = FALSE WHERE user_id = $1", user_id)
        row = await conn.fetchrow(
            """
            INSERT INTO presets (user_id, name, spot_ids, start_time, end_time, day_selection_type, day_selection_values, is_default)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING *;
            """,
            user_id, preset_data['name'], preset_data['spot_ids'], preset_data['start_time'],
            preset_data['end_time'], preset_data['day_selection_type'], preset_data['day_selection_values'],
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
        if updates.get('is_default'):
            await conn.execute("UPDATE presets SET is_default = FALSE WHERE user_id = $1 AND preset_id != $2", user_id, preset_id)
        set_clause = ", ".join(f"{key} = ${i + 3}" for i, key in enumerate(updates.keys()))
        query = f"UPDATE presets SET {set_clause} WHERE preset_id = $1 AND user_id = $2 RETURNING *;"
        values = [preset_id, user_id] + list(updates.values())
        updated_row = await conn.fetchrow(query, *values)
        if updated_row:
            updated_preset = dict(updated_row)
            updated_preset['user_id'] = str(updated_preset['user_id'])
            return updated_preset
        return None
    finally:
        await conn.close()

async def delete_preset(user_id: str, preset_id: int) -> bool:
    conn = await get_connection()
    try:
        result = await conn.execute("DELETE FROM presets WHERE preset_id = $1 AND user_id = $2", preset_id, user_id)
        return result.strip('DELETE ') == '1'
    finally:
        await conn.close()

# --- NOVA HIERARQUIA DE PREFERÊNCIAS ---

async def get_user_spot_preferences(user_id: str, spot_id: int) -> Optional[Dict[str, Any]]:
    """NÍVEL 1: Busca as preferências customizadas e ativas de um usuário para um spot."""
    conn = await get_connection()
    try:
        row = await conn.fetchrow(
            "SELECT * FROM user_spot_preferences WHERE user_id = $1 AND spot_id = $2 AND is_active = TRUE",
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

async def get_spot_level_preferences(spot_id: int, surf_level: str) -> Optional[Dict[str, Any]]:
    """NÍVEL 2: Busca as preferências padrão de um spot para um nível de surf."""
    conn = await get_connection()
    try:
        row = await conn.fetchrow(
            "SELECT * FROM spot_level_preferences WHERE spot_id = $1 AND surf_level = $2",
            spot_id, surf_level
        )
        return dict(row) if row else None
    finally:
        await conn.close()

async def get_generic_preferences_by_level(surf_level: str) -> Dict[str, Any]:
    """
    Retorna as preferências genéricas, agora com os 4 novos níveis.
    """
    # *** LÓGICA ATUALIZADA AQUI ***
    if surf_level == 'iniciante':
        return {
            "ideal_swell_height": 0.8, "max_swell_height": 1.2, "max_wind_speed": 4.0,
            "ideal_water_temperature": 24.0, "ideal_air_temperature": 26.0,
        }
    if surf_level == 'maroleiro':
        # Prefere ondas menores, mas com boa formação e pouco vento.
        return {
            "ideal_swell_height": 1.0, "max_swell_height": 1.5, "max_wind_speed": 5.0,
            "ideal_water_temperature": 23.0, "ideal_air_temperature": 25.0,
        }
    if surf_level == 'pro':
        # Busca condições mais desafiadoras.
        return {
            "ideal_swell_height": 2.2, "max_swell_height": 3.5, "max_wind_speed": 9.0,
            "ideal_water_temperature": 21.0, "ideal_air_temperature": 24.0,
        }
    # Padrão para 'intermediario'
    return {
        "ideal_swell_height": 1.5, "max_swell_height": 2.2, "max_wind_speed": 7.0,
        "ideal_water_temperature": 22.0, "ideal_air_temperature": 25.0,
    }

async def get_preferences_by_user_and_spot(user_id: str, spot_id: int) -> Dict[str, Any]:
    """
    Busca as preferências para um usuário e spot, garantindo valores para todos os campos.
    A hierarquia é:
    1. Preferências customizadas do usuário (user_spot_preferences)
    2. Preferências do pico por nível (spot_level_preferences)
    3. Preferências genéricas por nível (fallback)
    """
    user_profile = await get_profile_by_id(user_id)
    surf_level = user_profile.get('surf_level', 'intermediario') if user_profile else 'intermediario'

    # 1. Começa com as preferências genéricas como base
    final_prefs = await get_generic_preferences_by_level(surf_level)

    conn = await get_connection()
    try:
        # 2. Tenta sobrescrever com as preferências do pico
        spot_level_prefs_row = await conn.fetchrow(
            "SELECT * FROM spot_level_preferences WHERE spot_id = $1 AND surf_level = $2",
            spot_id, surf_level
        )
        if spot_level_prefs_row:
            spot_prefs = {k: v for k, v in dict(spot_level_prefs_row).items() if v is not None}
            final_prefs.update(spot_prefs)

        # 3. Tenta sobrescrever com as preferências do usuário (se ativas)
        user_prefs_row = await conn.fetchrow(
            "SELECT * FROM user_spot_preferences WHERE user_id = $1 AND spot_id = $2 AND is_active = TRUE",
            user_id, spot_id
        )
        if user_prefs_row:
            user_prefs = {k: v for k, v in dict(user_prefs_row).items() if v is not None}
            final_prefs.update(user_prefs)
            final_prefs.update({
                'preference_id': user_prefs_row['preference_id'],
                'is_active': user_prefs_row['is_active']
            })
    finally:
        await conn.close()

    final_prefs.setdefault('preference_id', 0)
    final_prefs.setdefault('user_id', user_id)
    final_prefs.setdefault('spot_id', spot_id)
    final_prefs.setdefault('is_active', False)

    return final_prefs


async def create_or_update_user_preferences(user_id: str, spot_id: int, updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Cria ou atualiza (UPSERT) as preferências de um usuário para um spot.
    """
    conn = await get_connection()
    try:
        set_clause = ", ".join(f"{key} = EXCLUDED.{key}" for key in updates.keys())

        # *** LINHA CORRIGIDA ***
        values_placeholders = ", ".join(f"${i + 3}" for i in range(len(updates)))

        query = f"""
        INSERT INTO user_spot_preferences (user_id, spot_id, {", ".join(updates.keys())})
        VALUES ($1, $2, {values_placeholders})
        ON CONFLICT (user_id, spot_id) DO UPDATE SET {set_clause}
        RETURNING *;
        """
        values = [user_id, spot_id] + list(updates.values())

        row = await conn.fetchrow(query, *values)

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

async def get_cached_recommendations(user_id: str, cache_key: str) -> Optional[List[Dict[str, Any]]]:
    """
    Busca as recomendações pré-calculadas usando uma chave de cache específica.
    """
    conn = await get_connection()
    try:
        row = await conn.fetchrow(
            # A query agora usa cache_key
            "SELECT recommendations_payload FROM user_recommendation_cache WHERE user_id = $1 AND cache_key = $2",
            user_id, cache_key
        )
        if row and row['recommendations_payload']:
            return json.loads(row['recommendations_payload'])
        return None
    finally:
        await conn.close()
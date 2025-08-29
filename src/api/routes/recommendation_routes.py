import numpy as np
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import datetime
from src.db.queries import (
    get_spot_by_id,
    get_user_by_id,
    get_spot_preferences,
    get_forecasts_from_db,
    get_level_spot_preferences
)
from src.recommendation.recommendation_logic import calculate_suitability_score
from src.utils.utils import convert_to_localtime_string

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

def convert_numpy_to_python_types(obj):
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: convert_numpy_to_python_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_to_python_types(elem) for elem in obj]
    elif isinstance(obj, (np.integer, np.floating, np.bool_)):
        return obj.item()
    return obj

class RecommendationRequest(BaseModel):
    user_id: str
    spot_ids: list[int]
    day_offset: list[int]
    start_time: str
    end_time: str

async def generate_recommendations_logic(user_id, spot_ids_list, day_offsets, start_time_str, end_time_str):
    user = await get_user_by_id(user_id)
    if not user:
        return {"error": f"Usuário com ID {user_id} não encontrado."}, 404
    surf_level = user.get('surf_level')
    if not surf_level:
        return {"error": f"Nível de surf não definido para o usuário {user_id}. Por favor, atualize seu perfil."}, 400
    try:
        # Verificar se os horários estão no formato HH:MM:SS e converter para HH:MM
        if len(start_time_str.split(":")) == 3:
            start_time_str = ":".join(start_time_str.split(":")[:2])
        if len(end_time_str.split(":")) == 3:
            end_time_str = ":".join(end_time_str.split(":")[:2])
            
        start_hour, start_minute = map(int, start_time_str.split(":"))
        end_hour, end_minute = map(int, end_time_str.split(":"))
    except ValueError as e:
        return {"error": f"Formato de hora inválido. Use HH:MM ou HH:MM:SS: {e}"}, 400

    all_spot_recommendations = []
    for spot_id in spot_ids_list:
        spot = await get_spot_by_id(spot_id)
        if not spot:
            all_spot_recommendations.append({
                "spot_name": f"Spot ID {spot_id}",
                "spot_id": spot_id,
                "error": f"Spot com ID {spot_id} não encontrado."
            })
            continue

        spot_recommendations_data = {
            "spot_name": spot['spot_name'],
            "spot_id": spot_id,
            "preferences_used_for_spot": {},
            "day_offsets": []
        }

        spot_preferences = await get_spot_preferences(user_id, spot_id, preference_type='user')
        if not spot_preferences:
            spot_preferences = await get_spot_preferences(user_id, spot_id, preference_type='model')
        if not spot_preferences:
            spot_preferences = await get_level_spot_preferences(surf_level, spot_id)
            if not spot_preferences:
                spot_recommendations_data["error"] = f"Nenhuma preferência configurada para o spot {spot['spot_name']} para este usuário/nível."
                all_spot_recommendations.append(spot_recommendations_data)
                continue
        spot_recommendations_data["preferences_used_for_spot"] = spot_preferences
        for day_offset_single in day_offsets:
            base_date_for_offset = datetime.datetime.utcnow().date() + datetime.timedelta(days=day_offset_single)
            start_utc = datetime.datetime.combine(base_date_for_offset, datetime.time(start_hour, start_minute)).replace(tzinfo=datetime.timezone.utc)
            end_utc = datetime.datetime.combine(base_date_for_offset, datetime.time(end_hour, end_minute, 59, 999999)).replace(tzinfo=datetime.timezone.utc)
            day_start = datetime.datetime.combine(base_date_for_offset, datetime.time.min).replace(tzinfo=datetime.timezone.utc)
            day_end = datetime.datetime.combine(base_date_for_offset, datetime.time.max).replace(tzinfo=datetime.timezone.utc)
            forecasts = await get_forecasts_from_db(spot_id, day_start, day_end)
            day_offset_data = {
                "day_offset": day_offset_single,
                "recommendations": []
            }
            if not forecasts:
                day_offset_data["error"] = f"Previsões não encontradas para o spot {spot['spot_name']} para o dia {day_offset_single}."
                spot_recommendations_data["day_offsets"].append(day_offset_data)
                continue
            filtered_forecasts = [
                f for f in forecasts
                if start_utc <= f['timestamp_utc'] <= end_utc
            ]
            if not filtered_forecasts:
                day_offset_data["error"] = f"Nenhuma previsão encontrada para o spot {spot['spot_name']} entre {start_time_str} e {end_time_str} para o dia {day_offset_single}."
                spot_recommendations_data["day_offsets"].append(day_offset_data)
                continue
            hourly_recommendations_for_day = []
            for forecast_entry in filtered_forecasts:
                tide_phase = forecast_entry.get('tide_type')
                suitability_score, detailed_scores = calculate_suitability_score(forecast_entry, spot_preferences, spot, tide_phase, user)
                recommendation_entry = {
                    "timestamp_utc": forecast_entry['timestamp_utc'].isoformat(),
                    "suitability_score": suitability_score,
                    "detailed_scores": detailed_scores,
                    "forecast_conditions": {
                        "wave_height_sg": forecast_entry.get('wave_height_sg'),
                        "wave_direction_sg": forecast_entry.get('wave_direction_sg'),
                        "wave_period_sg": forecast_entry.get('wave_period_sg'),
                        "swell_height_sg": forecast_entry.get('swell_height_sg'),
                        "swell_direction_sg": forecast_entry.get('swell_direction_sg'),
                        "swell_period_sg": forecast_entry.get('swell_period_sg'),
                        "secondary_swell_height_sg": forecast_entry.get('secondary_swell_height_sg'),
                        "secondary_swell_direction_sg": forecast_entry.get('secondary_swell_direction_sg'),
                        "secondary_swell_period_sg": forecast_entry.get('secondary_swell_period_sg'),
                        "wind_speed_sg": forecast_entry.get('wind_speed_sg'),
                        "wind_direction_sg": forecast_entry.get('wind_direction_sg'),
                        "water_temperature_sg": forecast_entry.get('water_temperature_sg'),
                        "air_temperature_sg": forecast_entry.get('air_temperature_sg'),
                        "current_speed_sg": forecast_entry.get('current_speed_sg'),
                        "current_direction_sg": forecast_entry.get('current_direction_sg'),
                        "sea_level_sg": forecast_entry.get('sea_level_sg'),
                        "tide_phase": tide_phase,
                    },
                    "spot_characteristics": {
                        "bottom_type": spot.get('bottom_type'),
                        "coast_orientation": spot.get('coast_orientation'),
                        "general_characteristics": spot.get('general_characteristics')
                    }
                }
                hourly_recommendations_for_day.append(recommendation_entry)
            day_offset_data["recommendations"] = hourly_recommendations_for_day
            spot_recommendations_data["day_offsets"].append(day_offset_data)
        all_spot_recommendations.append(spot_recommendations_data)
    return convert_numpy_to_python_types(all_spot_recommendations), 200

@router.post("")
async def get_recommendations_endpoint(request: RecommendationRequest):
    data = request.dict()
    user_id = data.get('user_id')
    spot_ids = data.get('spot_ids')
    day_offsets = data.get('day_offset')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    try:
        spot_ids = [int(s_id) for s_id in spot_ids]
    except (ValueError, TypeError) as e:
        raise HTTPException(status_code=400, detail="spot_ids deve ser uma lista de IDs de spots inteiros.")
    try:
        if not isinstance(day_offsets, list):
            day_offsets = [int(day_offsets)]
        else:
            day_offsets = [int(do) for do in day_offsets]
    except (ValueError, TypeError) as e:
        raise HTTPException(status_code=400, detail="day_offset deve ser um número inteiro ou uma lista de números inteiros.")
    recommendations_data, status_code = await generate_recommendations_logic(
        user_id, spot_ids, day_offsets, start_time, end_time
    )
    if status_code != 200:
        raise HTTPException(status_code=status_code, detail=recommendations_data)
    return recommendations_data
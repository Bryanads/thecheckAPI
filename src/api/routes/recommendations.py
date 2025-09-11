import datetime
import asyncio
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any

from src.core.schemas import Recommendation, RecommendationRequest 
from src.db import queries
from src.api.dependencies.auth import get_current_user_id
from src.services.scoring_service import calculate_overall_score

router = APIRouter(
    prefix="/recommendations",
    tags=["Recommendations"]
)

def weekdays_to_offsets(weekdays: List[int]) -> List[int]:
    """
    Converte uma lista de dias da semana (0=Dom, 6=Sáb) para offsets de dias
    a partir de hoje (0=hoje, 1=amanhã, etc.).
    """
    if not weekdays:
        return [0]
    
    today = datetime.datetime.now(datetime.timezone.utc).weekday()
    # No Python, weekday() é 0=Segunda, 6=Domingo. Ajustamos para 0=Domingo.
    today = (today + 1) % 7

    offsets = []
    for i in range(7):
        future_day = (today + i) % 7
        if future_day in weekdays:
            offsets.append(i)
    
    return offsets if offsets else [0]

@router.post("/", response_model=List[Recommendation])
async def get_recommendations(
    request: RecommendationRequest,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Gera uma lista classificada das melhores recomendações de surf
    com base nos critérios fornecidos.
    """
    # 1. Determinar os dias a serem buscados
    if request.day_selection.type == 'weekdays':
        day_offsets = weekdays_to_offsets(request.day_selection.values)
    else: # 'offsets'
        day_offsets = request.day_selection.values

    if not day_offsets:
        return []

    start_utc = datetime.datetime.now(datetime.timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    end_utc = start_utc + datetime.timedelta(days=max(day_offsets) + 1)

    # 2. Buscar todas as informações necessárias do banco de dados em paralelo
    user_profile_task = queries.get_profile_by_id(current_user_id)
    spot_tasks = {spot_id: queries.get_spot_by_id(spot_id) for spot_id in request.spot_ids}
    prefs_tasks = {spot_id: queries.get_preferences_by_user_and_spot(current_user_id, spot_id) for spot_id in request.spot_ids}
    forecast_tasks = {spot_id: queries.get_forecasts_for_spot(spot_id, start_utc, end_utc) for spot_id in request.spot_ids}
    
    user_profile, spots_details, preferences_details, forecasts_details = await asyncio.gather(
        user_profile_task,
        asyncio.gather(*spot_tasks.values()),
        asyncio.gather(*prefs_tasks.values()),
        asyncio.gather(*forecast_tasks.values())
    )

    # Mapeia de volta para dicionários para facilitar o acesso
    spots_map = {spot['spot_id']: spot for spot in spots_details}
    prefs_map = {pref['spot_id']: pref for pref in preferences_details if pref}
    forecasts_map = {sid: forecasts for sid, forecasts in zip(request.spot_ids, forecasts_details)}

    if not user_profile:
        raise HTTPException(status_code=404, detail="User profile not found")

    all_hourly_options = []

    # 3. Iterar sobre os resultados e calcular os scores
    for spot_id in request.spot_ids:
        spot_details = spots_map.get(spot_id)
        forecasts = forecasts_map.get(spot_id, [])
        
        user_prefs = prefs_map.get(spot_id)
        if not user_prefs:
            user_prefs = await queries.get_default_preferences_by_level(user_profile.get('surf_level', 'intermediario'))
        
        if not spot_details or not forecasts:
            continue

        for forecast in forecasts:
            forecast_time = forecast['timestamp_utc'].time()
            forecast_day_offset = (forecast['timestamp_utc'].date() - start_utc.date()).days

            # Filtra pelos dias e horários corretos
            if forecast_day_offset in day_offsets and request.time_window.start <= forecast_time <= request.time_window.end:
                score_data = await calculate_overall_score(forecast, user_prefs, spot_details, user_profile)
                
                all_hourly_options.append({
                    "spot_id": spot_id,
                    "spot_name": spot_details['name'],
                    "timestamp_utc": forecast['timestamp_utc'],
                    "forecast_conditions": forecast, 
                    **score_data
                })

    # 4. Ordenar e limitar os resultados
    sorted_recommendations = sorted(all_hourly_options, key=lambda x: x['overall_score'], reverse=True)
    
    return sorted_recommendations[:request.limit]
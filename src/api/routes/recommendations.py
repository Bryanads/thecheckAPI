# src/api/routes/recommendations.py

import datetime
import asyncio
import json
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from collections import defaultdict

from src.core.schemas import RecommendationRequest, DailyRecommendation, SpotDailySummary
from src.db import queries
from src.api.dependencies.auth import get_current_user_id
from src.services.scoring_service import calculate_overall_score
from .preferences import get_spot_preferences

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

def weekdays_to_offsets(weekdays: List[int]) -> List[int]:
    if not weekdays: return [0]
    today = (datetime.datetime.now(datetime.timezone.utc).weekday() + 1) % 7
    offsets = [i for i in range(7) if ((today + i) % 7) in weekdays]
    return offsets if offsets else [0]

# --- LÓGICA DE CÁLCULO EM TEMPO REAL (FALLBACK) ---
async def calculate_recommendations_realtime(
    request: RecommendationRequest,
    current_user_id: str,
    day_offsets: List[int]
) -> List[DailyRecommendation]:
    """ Lógica original de cálculo, agora usada como fallback. """
    print(f"INFO: Executando cálculo em tempo real para o usuário {current_user_id} com offsets {day_offsets}.")
    # (O restante desta função permanece o mesmo)
    start_utc = datetime.datetime.now(datetime.timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    end_utc = start_utc + datetime.timedelta(days=max(day_offsets) + 1)
    user_profile = await queries.get_profile_by_id(current_user_id)
    if not user_profile: raise HTTPException(status_code=404, detail="User profile not found")
    daily_options = defaultdict(list)
    for spot_id in request.spot_ids:
        spot_details, spot_forecasts, user_prefs = await asyncio.gather(queries.get_spot_by_id(spot_id), queries.get_forecasts_for_spot(spot_id, start_utc, end_utc), get_spot_preferences(spot_id, current_user_id))
        if not spot_details or not spot_forecasts: continue
        for forecast in spot_forecasts:
            forecast_time = forecast['timestamp_utc'].time()
            forecast_date = forecast['timestamp_utc'].date()
            forecast_day_offset = (forecast_date - start_utc.date()).days
            if forecast_day_offset in day_offsets and request.time_window.start <= forecast_time <= request.time_window.end:
                score_data = await calculate_overall_score(forecast, user_prefs, spot_details, user_profile)
                if score_data['overall_score'] > 30:
                    daily_options[forecast_date].append({"spot_id": spot_id, "spot_name": spot_details['name'],"timestamp_utc": forecast['timestamp_utc'], "forecast_conditions": forecast, **score_data})
    final_response = []
    for date, hourly_recs in sorted(daily_options.items()):
        best_spot_sessions = {}
        for rec in hourly_recs:
            sid = rec['spot_id']
            if sid not in best_spot_sessions or rec['overall_score'] > best_spot_sessions[sid]['best_overall_score']:
                best_spot_sessions[sid] = {"spot_id": sid, "spot_name": rec['spot_name'], "best_hour_utc": rec['timestamp_utc'], "best_overall_score": rec['overall_score'], "detailed_scores": rec['detailed_scores'], "forecast_conditions": rec['forecast_conditions']}
        if not best_spot_sessions: continue
        spot_summaries = [SpotDailySummary(**data) for data in best_spot_sessions.values()]
        ranked_spots_for_day = sorted(spot_summaries, key=lambda x: x.best_overall_score, reverse=True)
        final_response.append(DailyRecommendation(date=date, ranked_spots=ranked_spots_for_day))
    return final_response


@router.post("/", response_model=List[DailyRecommendation])
async def get_recommendations(
    request: RecommendationRequest,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Retorna recomendações. Se uma cache_key for fornecida, tenta servir do cache.
    Caso contrário, calcula em tempo real.
    """
    # --- NOVA LÓGICA SIMPLIFICADA ---
    if request.cache_key:
        print(f"INFO: Requisição com cache_key='{request.cache_key}'. Tentando buscar cache...")
        cached_data = await queries.get_cached_recommendations(current_user_id, request.cache_key)
        if cached_data is not None:
            print(f"INFO: Cache para '{request.cache_key}' encontrado e retornado.")
            return [DailyRecommendation.model_validate(item) for item in cached_data]
        else:
            print(f"AVISO: Cache para '{request.cache_key}' não encontrado. Acionando fallback.")
            # Se a chave foi fornecida mas o cache não existe, é melhor calcular em tempo real
            # usando os dados do preset que o frontend enviará.

    # --- LÓGICA DE FALLBACK (CÁLCULO EM TEMPO REAL) ---
    if request.day_selection.type == 'weekdays':
        day_offsets = weekdays_to_offsets(request.day_selection.values)
    else:
        day_offsets = request.day_selection.values

    if not day_offsets:
        return []

    return await calculate_recommendations_realtime(request, current_user_id, day_offsets)
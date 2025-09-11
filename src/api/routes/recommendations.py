# bryanads/thecheckapi/thecheckAPI-16b9a78c834b43d2ae715994e6bdff06b4aed85d/src/api/routes/recommendations.py
import datetime
import asyncio
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from collections import defaultdict

from src.core.schemas import RecommendationRequest, DailyRecommendation, SpotDailySummary
from src.db import queries
from src.api.dependencies.auth import get_current_user_id
from src.services.scoring_service import calculate_overall_score

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

def weekdays_to_offsets(weekdays: List[int]) -> List[int]:
    if not weekdays:
        return [0]
    
    today = datetime.datetime.now(datetime.timezone.utc).weekday()
    today = (today + 1) % 7

    offsets = []
    for i in range(7):
        future_day = (today + i) % 7
        if future_day in weekdays:
            offsets.append(i)
    
    return offsets if offsets else [0]

@router.post("/", response_model=List[DailyRecommendation])
async def get_recommendations(
    request: RecommendationRequest,
    current_user_id: str = Depends(get_current_user_id)
):
    if request.day_selection.type == 'weekdays':
        day_offsets = weekdays_to_offsets(request.day_selection.values)
    else:
        day_offsets = request.day_selection.values

    if not day_offsets:
        return []

    start_utc = datetime.datetime.now(datetime.timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    end_utc = start_utc + datetime.timedelta(days=max(day_offsets) + 1)

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

    spots_map = {spot['spot_id']: spot for spot in spots_details if spot}
    prefs_map = {pref['spot_id']: pref for pref in preferences_details if pref}
    forecasts_map = {sid: forecasts for sid, forecasts in zip(request.spot_ids, forecasts_details)}

    if not user_profile:
        raise HTTPException(status_code=404, detail="User profile not found")

    daily_options = defaultdict(list)

    for spot_id in request.spot_ids:
        spot_details = spots_map.get(spot_id)
        # CORREÇÃO AQUI: Acessar o dicionário correto
        spot_forecasts = forecasts_map.get(spot_id, [])
        
        user_prefs = prefs_map.get(spot_id)
        if not user_prefs or not user_prefs.get('is_active'):
            user_prefs = await queries.get_default_preferences_by_level(user_profile.get('surf_level', 'intermediario'))
            user_prefs.update({"user_id": current_user_id, "spot_id": spot_id, "preference_id": 0, "is_active": False})

        if not spot_details or not spot_forecasts:
            continue

        for forecast in spot_forecasts:
            forecast_time = forecast['timestamp_utc'].time()
            forecast_date = forecast['timestamp_utc'].date()
            forecast_day_offset = (forecast_date - start_utc.date()).days

            if forecast_day_offset in day_offsets and request.time_window.start <= forecast_time <= request.time_window.end:
                score_data = await calculate_overall_score(forecast, user_prefs, spot_details, user_profile)
                
                if score_data['overall_score'] > 30:
                    daily_options[forecast_date].append({
                        "spot_id": spot_id,
                        "spot_name": spot_details['name'],
                        "timestamp_utc": forecast['timestamp_utc'],
                        "forecast_conditions": forecast,
                        **score_data
                    })

    final_response = []
    for date, hourly_recs in sorted(daily_options.items()):
        
        best_spot_sessions = {}
        for rec in hourly_recs:
            spot_id = rec['spot_id']
            if spot_id not in best_spot_sessions or rec['overall_score'] > best_spot_sessions[spot_id].best_overall_score:
                best_spot_sessions[spot_id] = SpotDailySummary(
                    spot_id=rec['spot_id'],
                    spot_name=rec['spot_name'],
                    best_hour_utc=rec['timestamp_utc'],
                    best_overall_score=rec['overall_score'],
                    detailed_scores=rec['detailed_scores'],
                    forecast_conditions=rec['forecast_conditions']
                )
        
        if not best_spot_sessions:
            continue

        ranked_spots_for_day = sorted(best_spot_sessions.values(), key=lambda x: x.best_overall_score, reverse=True)

        final_response.append(DailyRecommendation(
            date=date,
            ranked_spots=ranked_spots_for_day
        ))
        
    return final_response
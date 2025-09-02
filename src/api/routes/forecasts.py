import datetime
import asyncio
from fastapi import APIRouter, HTTPException, status
from collections import defaultdict
from typing import List

from src.core.schemas import SpotForecastResponse, DailyForecast, HourlyData, ForecastConditions
from src.db import queries

router = APIRouter(
    prefix="/forecasts",
    tags=["Forecasts"]
)

@router.get("/spot/{spot_id}", response_model=SpotForecastResponse)
async def get_spot_forecast(spot_id: int):
    """
    Retorna a previsão bruta e detalhada, organizada por dia, 
    para os próximos 7 dias para um spot_id específico.
    """
    start_utc = datetime.datetime.now(datetime.timezone.utc)
    end_utc = start_utc + datetime.timedelta(days=7)

    spot_data_task = queries.get_spot_by_id(spot_id)
    forecast_rows_task = queries.get_forecasts_for_spot(spot_id, start_utc, end_utc)
    
    spot_data, forecast_rows = await asyncio.gather(spot_data_task, forecast_rows_task)

    if not spot_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Spot not found.")

    daily_forecasts_map = defaultdict(list)
    for row in forecast_rows:
        date = row['timestamp_utc'].date()
        
        # --- CORREÇÃO AQUI: Construção explícita do objeto ---
        # Em vez de **row, mapeamos cada campo para garantir a conversão correta.
        conditions_data = {
            "wave_height_sg": row.get("wave_height_sg"),
            "wave_direction_sg": row.get("wave_direction_sg"),
            "wave_period_sg": row.get("wave_period_sg"),
            "swell_height_sg": row.get("swell_height_sg"),
            "swell_direction_sg": row.get("swell_direction_sg"),
            "swell_period_sg": row.get("swell_period_sg"),
            "secondary_swell_height_sg": row.get("secondary_swell_height_sg"),
            "secondary_swell_direction_sg": row.get("secondary_swell_direction_sg"),
            "secondary_swell_period_sg": row.get("secondary_swell_period_sg"),
            "wind_speed_sg": row.get("wind_speed_sg"),
            "wind_direction_sg": row.get("wind_direction_sg"),
            "water_temperature_sg": row.get("water_temperature_sg"),
            "air_temperature_sg": row.get("air_temperature_sg"),
            "current_speed_sg": row.get("current_speed_sg"),
            "current_direction_sg": row.get("current_direction_sg"),
            "sea_level_sg": row.get("sea_level_sg"),
            "tide_type": row.get("tide_type")
        }
        
        hourly_data = HourlyData(
            timestamp_utc=row['timestamp_utc'],
            conditions=ForecastConditions(**conditions_data)
        )
        daily_forecasts_map[date].append(hourly_data)

    daily_forecasts_list = [
        DailyForecast(date=date, hourly_data=hourly_list)
        for date, hourly_list in sorted(daily_forecasts_map.items())
    ]
    
    return SpotForecastResponse(
        spot_id=spot_id,
        spot_name=spot_data['name'],
        daily_forecasts=daily_forecasts_list
    )
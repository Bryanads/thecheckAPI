# bryanads/thecheckapi/thecheckAPI-16b9a78c834b43d2ae715994e6bdff06b4aed85d/src/api/routes/forecasts.py
import datetime
import asyncio
from fastapi import APIRouter, HTTPException, status
from typing import List

from src.core.schemas import SpotForecastResponse, HourlyData, ForecastConditions
from src.db import queries

router = APIRouter(
    prefix="/forecasts",
    tags=["Forecasts"]
)

@router.get("/spot/{spot_id}", response_model=SpotForecastResponse)
async def get_spot_forecast(spot_id: int):
    """
    Retorna uma lista contínua de previsões horárias para os próximos 7 dias
    e as últimas 24 horas para um spot_id específico.
    """
    # MODIFICAÇÃO 1: Começa a busca 24 horas no passado
    start_utc = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)
    end_utc = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)

    spot_data_task = queries.get_spot_by_id(spot_id)
    forecast_rows_task = queries.get_forecasts_for_spot(spot_id, start_utc, end_utc)
    
    spot_data, forecast_rows = await asyncio.gather(spot_data_task, forecast_rows_task)

    if not spot_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Spot not found.")

    # MODIFICAÇÃO 2: Não agrupa mais por dia, apenas converte os resultados
    hourly_forecasts = []
    for row in forecast_rows:
        conditions_data = {k: v for k, v in row.items() if k not in ['forecast_id', 'spot_id', 'timestamp_utc', 'last_modified_at']}
        
        hourly_data = HourlyData(
            timestamp_utc=row['timestamp_utc'],
            conditions=ForecastConditions(**conditions_data)
        )
        hourly_forecasts.append(hourly_data)
    
    return SpotForecastResponse(
        spot_id=spot_id,
        spot_name=spot_data['name'],
        forecasts=hourly_forecasts # Retorna a lista contínua
    )
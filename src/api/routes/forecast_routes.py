from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import datetime
from src.db.queries import get_spot_by_id, get_forecasts_from_db

router = APIRouter(prefix="/forecasts", tags=["forecasts"])

class ForecastRequest(BaseModel):
    spot_ids: list[int]
    day_offset: list[int]

@router.post("")
async def get_combined_forecasts_endpoint(request: ForecastRequest):
    data = request.dict()
    spot_ids = data["spot_ids"]
    day_offsets = data["day_offset"]

    flat_forecast_entries = []
    has_errors = False
    error_messages = []

    for day_offset in day_offsets:
        base_date = datetime.datetime.now(datetime.timezone.utc).date() + datetime.timedelta(days=day_offset)
        start_utc = datetime.datetime.combine(base_date, datetime.time.min).replace(tzinfo=datetime.timezone.utc)
        end_utc = datetime.datetime.combine(base_date, datetime.time.max).replace(tzinfo=datetime.timezone.utc)

        for spot_id in spot_ids:
            spot = await get_spot_by_id(spot_id)
            if not spot:
                error_messages.append(f"Spot com ID {spot_id} não encontrado.")
                has_errors = True
                continue

            forecasts = await get_forecasts_from_db(spot_id, start_utc, end_utc)

            if not forecasts:
                error_messages.append(f"Previsões não encontradas para o spot {spot_id} na data {base_date.isoformat()}.")
                has_errors = True
            else:
                for forecast_entry in forecasts:
                    entry_with_spot_and_tide = {
                        "spot_id": spot_id,
                        "spot_name": spot['spot_name'],
                        "latitude": spot['latitude'],
                        "longitude": spot['longitude'],
                        "timezone": spot['timezone'],
                        "tide_type": forecast_entry.get('tide_type'),
                        **forecast_entry
                    }
                    flat_forecast_entries.append(entry_with_spot_and_tide)

    if has_errors:
        return JSONResponse(status_code=207, content={"message": "Alguns dados não puderam ser recuperados.", "errors": error_messages, "data": flat_forecast_entries})
    return flat_forecast_entries
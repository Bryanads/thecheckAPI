import datetime
from pydantic import BaseModel, EmailStr
from typing import List, Optional

class Spot(BaseModel):
    spot_id: int
    name: str
    latitude: float
    longitude: float
    timezone: str
    bottom_type: Optional[str] = None
    break_type: Optional[str] = None
    difficulty_level: Optional[str] = None
    state: Optional[str] = None
    region: Optional[str] = None
    ideal_swell_direction: Optional[List[float]] = None
    ideal_wind_direction: Optional[List[float]] = None
    ideal_sea_level: Optional[float] = None
    ideal_tide_flow: Optional[List[str]] = None

    class Config:
        from_attributes = True

class Profile(BaseModel):
    id: str 
    name: str
    email: EmailStr
    location: Optional[str] = None
    bio: Optional[str] = None
    surf_level: Optional[str] = None
    stance: Optional[str] = None

    class Config:
        from_attributes = True


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    bio: Optional[str] = None
    surf_level: Optional[str] = None
    stance: Optional[str] = None



class PresetBase(BaseModel):
    name: str
    spot_ids: List[int]
    start_time: datetime.time
    end_time: datetime.time
    day_selection_type: str 
    day_selection_values: List[int]
    is_default: bool = False

class PresetCreate(PresetBase):
    pass

class PresetUpdate(BaseModel):
    name: Optional[str] = None
    spot_ids: Optional[List[int]] = None
    start_time: Optional[datetime.time] = None
    end_time: Optional[datetime.time] = None
    day_selection_type: Optional[str] = None
    day_selection_values: Optional[List[int]] = None
    is_default: Optional[bool] = None

class Preset(PresetBase):
    preset_id: int
    user_id: str 

    class Config:
        from_attributes = True

class PreferenceUpdate(BaseModel):
    ideal_swell_height: Optional[float] = None
    max_swell_height: Optional[float] = None
    max_wind_speed: Optional[float] = None
    ideal_water_temperature: Optional[float] = None
    ideal_air_temperature: Optional[float] = None
    is_active: Optional[bool] = None

class Preference(BaseModel):
    preference_id: int
    user_id: str
    spot_id: int
    ideal_swell_height: Optional[float] = None
    max_swell_height: Optional[float] = None
    max_wind_speed: Optional[float] = None
    ideal_water_temperature: Optional[float] = None
    ideal_air_temperature: Optional[float] = None
    is_active: bool

    class Config:
        from_attributes = True


class ForecastConditions(BaseModel):
    wave_height_sg: Optional[float] = None
    wave_direction_sg: Optional[float] = None
    wave_period_sg: Optional[float] = None
    swell_height_sg: Optional[float] = None
    swell_direction_sg: Optional[float] = None
    swell_period_sg: Optional[float] = None
    secondary_swell_height_sg: Optional[float] = None
    secondary_swell_direction_sg: Optional[float] = None
    secondary_swell_period_sg: Optional[float] = None
    wind_speed_sg: Optional[float] = None
    wind_direction_sg: Optional[float] = None
    water_temperature_sg: Optional[float] = None
    air_temperature_sg: Optional[float] = None
    current_speed_sg: Optional[float] = None
    current_direction_sg: Optional[float] = None
    sea_level_sg: Optional[float] = None
    tide_type: Optional[str] = None

class HourlyData(BaseModel):
    timestamp_utc: datetime.datetime
    conditions: ForecastConditions

class DailyForecast(BaseModel):
    date: datetime.date
    hourly_data: List[HourlyData]

class SpotForecastResponse(BaseModel):
    spot_id: int
    spot_name: str
    forecasts: List[HourlyData]


class DaySelection(BaseModel):
    type: str 
    values: List[int]

class TimeWindow(BaseModel):
    start: datetime.time
    end: datetime.time

class RecommendationRequest(BaseModel):
    spot_ids: List[int]
    day_selection: DaySelection
    time_window: TimeWindow
    limit: Optional[int] = None # Tornando o limite opcional

class DetailedScores(BaseModel):
    wave_score: float
    wind_score: float
    tide_score: float
    air_temperature_score: float
    water_temperature_score: float

# --- NOVOS SCHEMAS PARA A RESPOSTA DE RECOMENDAÇÃO ---

class HourlyRecommendation(BaseModel):
    spot_id: int
    spot_name: str
    timestamp_utc: datetime.datetime
    overall_score: float
    detailed_scores: DetailedScores
    forecast_conditions: ForecastConditions

class DayOffsetRecommendations(BaseModel):
    day_offset: int
    recommendations: List[HourlyRecommendation]

class SpotRecommendation(BaseModel):
    spot_id: int
    spot_name: str
    preferences_used_for_spot: Preference
    day_offsets: List[DayOffsetRecommendations]
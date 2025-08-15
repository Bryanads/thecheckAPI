import numpy as np

from src.recommendation.wind_score import calcular_score_vento
from src.recommendation.tide_score import calcular_score_mare
from src.recommendation.current_score import calcular_score_corrente
from src.recommendation.temperature_score import (
    calcular_score_temperatura_agua,
    calcular_score_temperatura_ar
)
from src.recommendation.wave_score import (
    calcular_score_onda
)
def calculate_suitability_score(forecast_entry, spot_preferences, spot_info, tide_phase, user_info):
    """
    Calcula um score de adequação geral para o surf com base nas previsões e preferências.

    Args:
        forecast_entry (dict): Dados de previsão para um determinado timestamp.
        spot_preferences (dict): Preferências de surf para o spot (do usuário ou padrão).
        spot_info (dict): Informações estáticas sobre o spot (tipo de fundo, orientação, etc.).
        tide_phase (str): Fase da maré determinada ('enchente', 'vazante', 'pico_alta', 'pico_baixa').
        user_info (dict): Informações do usuário (nível de surf, etc.).

    Returns:
        tuple: Um tuple contendo:
            - float: O score de adequação geral (0 a 1).
            - dict: Um dicionário com os scores detalhados de cada critério.
    """

    detailed_scores = {}

    """
    -----------------------------------------------------------------------------------------------
    ------------------------------------------Scores Onda------------------------------------------
    -----------------------------------------------------------------------------------------------
    """
    # Parâmetros da Previsão
    previsao_tamanho = float(forecast_entry.get('wave_height_sg')) if forecast_entry.get('wave_height_sg') is not None else None
    previsao_direcao = float(forecast_entry.get('wave_direction_sg')) if forecast_entry.get('wave_direction_sg') is not None else None
    previsao_periodo = float(forecast_entry.get('wave_period_sg')) if forecast_entry.get('wave_period_sg') is not None else None
    
    previsao_sec_tamanho = float(forecast_entry.get('secondary_swell_height_sg', 0.0))
    previsao_sec_direcao = float(forecast_entry.get('secondary_swell_direction_sg', 0.0))
    previsao_sec_periodo = float(forecast_entry.get('secondary_swell_period_sg', 0.0))

    tamanho_minimo = float(spot_preferences.get('min_wave_height', 0.5))
    tamanho_ideal = float(spot_preferences.get('ideal_wave_height', 1.5))
    tamanho_maximo = float(spot_preferences.get('max_wave_height', 2.5))
    direcao_ideal = float(spot_preferences.get('ideal_wave_direction', 180.0))
    periodo_ideal = float(spot_preferences.get('ideal_wave_period', 10.0))

    score_onda = 0 # Score padrão caso os dados essenciais não existam

    if all(v is not None for v in [previsao_tamanho, previsao_direcao, previsao_periodo]):
        score_onda_result = calcular_score_onda(
            previsao_tamanho, previsao_direcao, previsao_periodo,
            tamanho_minimo, tamanho_ideal, tamanho_maximo,
            direcao_ideal, periodo_ideal,
            previsao_sec_tamanho, previsao_sec_direcao, previsao_sec_periodo
        )
        score_onda = float(score_onda_result.item()) if isinstance(score_onda_result, np.ndarray) else float(score_onda_result)
    
    detailed_scores['wave_score'] = score_onda
    

    """
    -----------------------------------------------------------------------------------------------
    ------------------------------------------Score Vento------------------------------------------
    -----------------------------------------------------------------------------------------------
    """

    wind_speed = float(forecast_entry.get('wind_speed_sg')) if forecast_entry.get('wind_speed_sg') is not None else None
    wind_dir = float(forecast_entry.get('wind_direction_sg')) if forecast_entry.get('wind_direction_sg') is not None else None
    preferred_wind_dir = float(spot_preferences.get('ideal_wind_direction', 0.0))
    ideal_wind_speed = float(spot_preferences.get('ideal_wind_speed', 5.0))
    max_wind_speed = float(spot_preferences.get('max_wind_speed', 20.0))

    score_vento = 0.0

    if all(v is not None for v in [wind_speed, wind_dir, preferred_wind_dir, ideal_wind_speed, max_wind_speed]):
        score_vento_result = calcular_score_vento(
            wind_speed,
            wind_dir,
            preferred_wind_dir,
            ideal_wind_speed,
            max_wind_speed
        )
        score_vento = float(score_vento_result.item()) if isinstance(score_vento_result, np.ndarray) else float(score_vento_result)
    detailed_scores['wind_score'] = score_vento

    """
    -----------------------------------------------------------------------------------------------
    ------------------------------------------Score Maré------------------------------------------
    -----------------------------------------------------------------------------------------------
    """
    previsao_mare = forecast_entry.get('sea_level_sg') # Altura da maré
    mare_ideal = float(spot_preferences.get('ideal_tide_height', 0.0)) # Converter para float
    mare_tipo_ideal = spot_preferences.get('ideal_tide_type') # 'qualquer', 'enchente', 'vazante', etc.

    score_mare = 0.0

    if all(v is not None for v in [previsao_mare, mare_ideal, tide_phase, mare_tipo_ideal]):
        score_mare_result = calcular_score_mare(
            previsao_mare,
            mare_ideal,
            tide_phase, # A fase da maré atual para comparação
            mare_tipo_ideal
        )
        score_mare = float(score_mare_result.item()) if isinstance(score_mare_result, np.ndarray) else float(score_mare_result)
    detailed_scores['tide_score'] = score_mare

    """
    -----------------------------------------------------------------------------------------------
    ---------------------------------------Scores Temperatura---------------------------------------
    -----------------------------------------------------------------------------------------------
    """
    #------------------------------------SCORE TEMPERATURA ÁGUA------------------------------------
    water_temp = forecast_entry.get('water_temperature_sg')
    ideal_water_temp = float(spot_preferences.get('ideal_water_temperature', 22.0)) # Converter para float

    score_temperatura_agua = 0.0
    
    if water_temp is not None and ideal_water_temp is not None:
        score_temperatura_agua_result = calcular_score_temperatura_agua(
            water_temp,
            ideal_water_temp
        )
        score_temperatura_agua = float(score_temperatura_agua_result.item()) if isinstance(score_temperatura_agua_result, np.ndarray) else float(score_temperatura_agua_result)
    detailed_scores['water_temperature_score'] = score_temperatura_agua

    #------------------------------------SCORE TEMPERATURA AR------------------------------------
    air_temp = forecast_entry.get('air_temperature_sg')
    ideal_air_temp = float(spot_preferences.get('ideal_air_temperature', 25.0)) # Converter para float

    score_temperatura_ar = 0.0

    if air_temp is not None and ideal_air_temp is not None:
        score_temperatura_ar_result = calcular_score_temperatura_ar(
            air_temp,
            ideal_air_temp
        )
        score_temperatura_ar = float(score_temperatura_ar_result.item()) if isinstance(score_temperatura_ar_result, np.ndarray) else float(score_temperatura_ar_result)
    detailed_scores['air_temperature_score'] = score_temperatura_ar

    """
    -----------------------------------------------------------------------------------------------
    -----------------------------------------Scores Corrente-----------------------------------------
    -----------------------------------------------------------------------------------------------
    """
    current_speed = forecast_entry.get('current_speed_sg')
    # O spot_preferences pode ter 'ideal_current_speed', mas um default de 0.0 é razoável
    ideal_current_speed = float(spot_preferences.get('ideal_current_speed', 0.0))

    score_corrente = 0.0

    if current_speed is not None and ideal_current_speed is not None:
        score_corrente_result = calcular_score_corrente(
            current_speed,
            ideal_current_speed
        )
        score_corrente = float(score_corrente_result.item()) if isinstance(score_corrente_result, np.ndarray) else float(score_corrente_result)
    detailed_scores['current_score'] = score_corrente


    """
    -----------------------------------------------------------------------------------------------
    ---------------------------------------Cálculo Final-------------------------------------------
    -----------------------------------------------------------------------------------------------
    """
    # Define os pesos de cada fator. A soma deve ser 1.0.
    # Onda e Vento são os mais críticos para a qualidade do surf.
    weights = {
        'wave': 0.50,   # 50% - O fator mais importante.
        'wind': 0.25,   # 25% - O segundo mais importante, define a formação da onda.
        'tide': 0.15,   # 15% - Crucial para a maioria dos picos.
        'current': 0.05,# 5% - Pode ajudar ou atrapalhar significativamente.
        'water_temp': 0.03, # 3% - Fator de conforto.
        'air_temp': 0.02,   # 2% - Fator de conforto.
    }
    
    # Como todos os scores estão na mesma escala (-100 a 100), podemos fazer a média ponderada.
    # Lembre-se que chegamos aqui apenas se score_onda >= 0.
    final_suitability_score = (
        score_onda * weights['wave'] +
        score_vento * weights['wind'] +
        score_mare * weights['tide'] +
        score_corrente * weights['current'] +
        score_temperatura_agua * weights['water_temp'] +
        score_temperatura_ar * weights['air_temp']
    )
    
    # Arredonda o score final para manter a consistência.
    final_suitability_score = np.clip(final_suitability_score, 0, 100)  # Garante que o score esteja no intervalo esperado
    final_suitability_score = round(final_suitability_score, 2)

    return float(final_suitability_score), detailed_scores

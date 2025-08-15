import numpy as np

def calcular_score_temperatura_agua(
    water_temp,
    ideal_water_temp
):
    """
    Calcula um score para a temperatura da água.

    O score é 1.0 na temperatura ideal e decai à medida que a temperatura se afasta,
    seja para mais frio ou para mais quente.

    Args:
        water_temp (float or np.ndarray): Temperatura atual da água em graus Celsius.
        ideal_water_temp (float): Temperatura da água considerada ideal em graus Celsius.

    Returns:
        float or np.ndarray: Score da temperatura da água, entre 0 e 1.
    """
    water_temp = np.asarray(water_temp, dtype=float)
    ideal_water_temp = float(ideal_water_temp) # Converter para float

    # --- Fator de decaimento fixo para temperatura da água ---
    # Ajuste este valor para controlar a inclinação da curva da água.
    # Quanto maior, mais rápido o score decai da temperatura ideal.
    decay_rate_agua = 0.08

    # Calcular a diferença absoluta em relação à temperatura ideal
    temp_diff = np.abs(water_temp - ideal_water_temp)

    # Usar uma função exponencial decrescente simples.
    scores = np.exp(-decay_rate_agua * (temp_diff**2))

    # Garantir que o score esteja sempre entre 0 e 1
    scores = np.clip(scores, 0.0, 1.0)

    scores = scores * 100
    scores = np.round(scores, 2)

    return scores

def calcular_score_temperatura_ar(
    air_temp,
    ideal_air_temp
):
    """
    Calcula um score para a temperatura do ar.

    O score é 1.0 na temperatura ideal e decai à medida que a temperatura se afasta,
    seja para mais frio ou para mais quente.

    Args:
        air_temp (float or np.ndarray): Temperatura atual do ar em graus Celsius.
        ideal_air_temp (float): Temperatura do ar considerada ideal em graus Celsius.

    Returns:
        float or np.ndarray: Score da temperatura do ar, entre 0 e 1.
    """
    air_temp = np.asarray(air_temp, dtype=float)
    ideal_air_temp = float(ideal_air_temp) # Converter para float

    # --- Fator de decaimento fixo para temperatura do ar ---
    # Ajuste este valor para controlar a inclinação da curva do ar.
    # Quanto maior, mais rápido o score decai da temperatura ideal.
    decay_rate_ar = 0.04

    # Calcular a diferença absoluta em relação à temperatura ideal
    temp_diff = np.abs(air_temp - ideal_air_temp)

    # Usar uma função exponencial decrescente simples.
    scores = np.exp(-decay_rate_ar * (temp_diff**2))

    # Garantir que o score esteja sempre entre 0 e 1
    scores = np.clip(scores, 0.0, 1.0)

    scores = scores * 100
    scores = np.round(scores, 2)

    return scores
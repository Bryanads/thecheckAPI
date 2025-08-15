import numpy as np


def calcular_score_vento(
    wind_speed,
    wind_dir,
    preferred_wind_dir,
    ideal_wind_speed,
    max_wind_speed
):
    """
    Calcula um score para o vento, com uma fase extra de penalidade para ventos > max_wind_speed.
    - A penalidade pós-max_wind_speed é mais branda para o terral e mais severa para o maral.
    """
    wind_speed = np.asarray(wind_speed, dtype=float)
    wind_dir = np.asarray(wind_dir, dtype=float)

    angle_diff = np.abs(wind_dir - preferred_wind_dir)
    angle_diff = np.minimum(angle_diff, 360 - angle_diff)
    is_ideal_direction = angle_diff <= 45

    scores = np.zeros_like(wind_speed, dtype=float)
    
    # --- MÁSCARA PARA VELOCIDADES ATÉ O MAX_WIND_SPEED ---
    mask_normal_range = wind_speed <= max_wind_speed

    # --- Lógica para Vento com Direção Ideal (Terral/Offshore) ---
    mask_ideal = is_ideal_direction
    if np.any(mask_ideal):
        # 1. De 0 a ideal_wind_speed: sobe de 75 para 100
        mask_good = (wind_speed <= ideal_wind_speed) & mask_ideal & mask_normal_range
        if ideal_wind_speed > 0:
            scores[mask_good] = 75 + (wind_speed[mask_good] / ideal_wind_speed) * 25

        # 2. De ideal_wind_speed a max_wind_speed: cai de 100 para 0
        mask_falling = (wind_speed > ideal_wind_speed) & mask_ideal & mask_normal_range
        denominator = max_wind_speed - ideal_wind_speed
        if denominator > 0:
            fator_norm = (wind_speed[mask_falling] - ideal_wind_speed) / denominator
            scores[mask_falling] = 100 - 100 * fator_norm

    # --- Lógica para Vento com Direção Não-Ideal (Maral/Onshore) ---
    mask_non_ideal = ~is_ideal_direction
    if np.any(mask_non_ideal):
        # Reta única de 75 para 0 até o max_wind_speed
        mask_maral_normal = mask_non_ideal & mask_normal_range
        if max_wind_speed > 0:
            scores[mask_maral_normal] = 75 - (wind_speed[mask_maral_normal] / max_wind_speed) * 75

    mask_extreme_range = wind_speed > max_wind_speed
    if np.any(mask_extreme_range):
        # Para o vento terral, a penalidade é mais lenta.
        # Vamos definir que ele atinge -100 em 1.5x max_wind_speed
        mask_extreme_ideal = mask_extreme_range & mask_ideal
        denominator_ideal = (max_wind_speed * 1.5) - max_wind_speed
        if denominator_ideal > 0:
            fator_norm = (wind_speed[mask_extreme_ideal] - max_wind_speed) / denominator_ideal
            scores[mask_extreme_ideal] = -100 * fator_norm

        # Vamos definir que ele atinge -100 em 1.2x max_wind_speed
        mask_extreme_non_ideal = mask_extreme_range & mask_non_ideal
        denominator_non_ideal = (max_wind_speed * 1.2) - max_wind_speed
        if denominator_non_ideal > 0:
            fator_norm = (wind_speed[mask_extreme_non_ideal] - max_wind_speed) / denominator_non_ideal
            scores[mask_extreme_non_ideal] = -100 * fator_norm


    scores[wind_speed == 0] = 75
    scores = np.clip(scores, -100.0, 100.0)
    scores = np.round(scores, 2)
    return scores
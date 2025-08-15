import numpy as np

def calcular_score_corrente(
    current_speed,
    ideal_current_speed=0.0 # Valor padrão para corrente ideal (nula ou muito fraca)
):
    """
    Calcula um score para a velocidade da correnteza.

    O score é 1.0 na velocidade ideal (ou seja, nula/muito fraca) e decai
    à medida que a correnteza se torna mais forte. A direção não é um fator aqui,
    apenas a magnitude da correnteza.

    Args:
        current_speed (float or np.ndarray): Velocidade atual da correnteza (e.g., m/s ou nós).
        ideal_current_speed (float): Velocidade da correnteza considerada ideal (próximo de zero).

    Returns:
        float or np.ndarray: Score da correnteza, entre 0 e 1.
    """
    current_speed = np.asarray(current_speed, dtype=float)
    ideal_current_speed = float(ideal_current_speed)

    # --- Fator de decaimento para correnteza ---
    # Este valor determina quão rapidamente o score da correnteza cai
    # à medida que a velocidade se afasta do ideal (próximo de zero).
    # Um valor maior penaliza mais fortemente correntes mais rápidas.
    # A velocidade de 0.5 m/s é usada como referência para a escala do decaimento.
    # Ajuste este valor (ex: 0.5) para controlar a sensibilidade.
    decay_factor_corrente = 0.5 # Corresponde a uma corrente de 0.5 m/s, após isso a queda é mais acentuada.

    # Calcula a diferença da velocidade da corrente em relação ao ideal.
    # Geralmente, a corrente ideal é 0 (ou muito próxima de zero).
    current_speed_diff = np.abs(current_speed - ideal_current_speed)

    # Usa uma função exponencial decrescente para o score.
    # A corrente ideal (ou próxima de zero) recebe score máximo (próximo de 1).
    # Correntes mais fortes (maior current_speed_diff) reduzem o score.
    scores = np.exp(-current_speed_diff / decay_factor_corrente)

    # Garante que o score esteja sempre entre 0 e 1
    scores = np.clip(scores, 0.0, 1.0)

    scores = scores * 100
    scores = np.round(scores, 2)

    return scores
import numpy as np

def calcular_score_mare(previsao_mare, mare_ideal, mare_tipo_previsao, mare_tipo_ideal):
    """
    Calcula um score para a maré usando uma curva hiperbólica para a altura
    e ajustando com base no tipo de maré.

    Args:
        previsao_mare (np.array ou float): A altura da maré prevista (em metros). Pode ser um array.
        mare_ideal (float): A altura da maré considerada ideal (em metros).
        mare_tipo_previsao (np.array ou str): O tipo da maré prevista ('enchente', 'vazante', 'pico_alta', 'pico_baixa'). Pode ser um array.
        mare_tipo_ideal (str): O tipo da maré ideal ('qualquer', 'enchente', 'vazante', 'pico_alta', 'pico_baixa').

    Returns:
        np.array ou float: Um score de 0 a 1, onde 1 indica condições ideais de maré e 0 indica condições desfavoráveis.
    """
    previsao_mare = np.asarray(previsao_mare, dtype=float)
    mare_ideal = float(mare_ideal)
    # Garante que mare_tipo_previsao seja um array de strings, mas pode vir como escalar
    if isinstance(mare_tipo_previsao, str):
        mare_tipo_previsao_arr = np.array([mare_tipo_previsao], dtype=str)
    else:
        mare_tipo_previsao_arr = np.asarray(mare_tipo_previsao, dtype=str)
        
    mare_tipo_ideal = str(mare_tipo_ideal)

    # Calcula o score base da altura da maré usando a função exponencial (curva hiperbólica)
    # A base 'mare_ideal' no denominador controla a sensibilidade da queda do score
    # quanto maior 'mare_ideal', mais "flat" a curva, ou seja, menos sensível a variações
    # Se 'mare_ideal' for 0, podemos ter um problema de divisão por zero.
    # Para evitar isso, adicionamos uma pequena constante se mare_ideal for muito próximo de zero
    if mare_ideal <= 0: 
        score_altura = np.exp(-((previsao_mare - mare_ideal) ** 2) / 0.1) # Usando um valor pequeno fixo
    else:
        score_altura = np.exp(-((previsao_mare - mare_ideal) ** 2) / mare_ideal)

    # Inicializa o score final com o score da altura
    score_final = score_altura

    # Aplica a lógica de penalidade baseada no tipo de maré ideal
    if mare_tipo_ideal != 'qualquer':
        # Cria uma máscara booleana para comparar os tipos de maré
        tipos_correspondem = (mare_tipo_previsao_arr == mare_tipo_ideal)

        # Aplica a penalidade: se os tipos não correspondem, multiplica o score da altura por 0.8
        # np.where permite aplicar a condição em arrays
        score_final = np.where(tipos_correspondem, score_altura, score_altura * 0.8)
    
    # Garante que o score final esteja entre 0 e 1
    score_final = np.clip(score_final, 0.0, 1.0)

    score_final = score_final * 100
    score_final = np.round(score_final, 2)

    return score_final
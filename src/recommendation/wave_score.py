import numpy as np

def calcular_score_tamanho_onda(
    previsao_onda, tamanho_minimo, tamanho_ideal, tamanho_maximo
):
    """
    Calcula o score do tamanho da onda usando curvas suaves para uma representação mais realista.

    - Abaixo do mínimo: Curva quadrática suave de 0 a -100.
    - Mínimo ao Ideal: Curva senoidal crescente de 0 a 100 para uma subida suave.
    - Ideal ao Máximo: Curva cossenoidal decrescente de 100 a 0 para uma queda suave.
    - Acima do máximo: Decaimento exponencial de 0 a -100 para refletir o aumento do risco.
    """
    previsao_onda = np.asarray(previsao_onda, dtype=float)
    score = np.zeros_like(previsao_onda)

    # --- Seção 1: Onda menor que o limite mínimo (Flat a Pequeno) ---
    # A penalidade aumenta quadraticamente à medida que a onda se afasta (para baixo) do mínimo.
    # Isso cria uma curva suave que penaliza mais fortemente ondas muito pequenas.
    mask1 = previsao_onda < tamanho_minimo
    if tamanho_minimo > 0:
        # Normaliza a distância do mínimo e eleva ao quadrado para a curva.
        # O resultado vai de 0 (no tamanho_minimo) a -1 (em 0m).
        score[mask1] = -(((tamanho_minimo - previsao_onda[mask1]) / tamanho_minimo) ** 2)

    # --- Seção 2: Onda entre o limite mínimo e o ideal (Na medida certa) ---
    # Usamos meio período de uma onda senoidal para uma transição suave de 0 a 1.
    # O expoente 1.5 faz a curva subir um pouco mais rápido no início, refletindo
    # a empolgação de sair do "muito pequeno" para o "bom".
    mask2 = (previsao_onda >= tamanho_minimo) & (previsao_onda <= tamanho_ideal)
    if tamanho_ideal > tamanho_minimo:
        fator_normalizado = (previsao_onda[mask2] - tamanho_minimo) / (tamanho_ideal - tamanho_minimo)
        score[mask2] = np.sin(fator_normalizado * np.pi / 2) ** 1.5

    # --- Seção 3: Onda entre o ideal e o limite máximo (Grande mas ainda bom) ---
    # Usamos meio período de uma onda cossenoidal para uma transição suave de 1 a 0.
    # Isso conecta perfeitamente com o pico da seção anterior.
    mask3 = (previsao_onda > tamanho_ideal) & (previsao_onda <= tamanho_maximo)
    if tamanho_maximo > tamanho_ideal:
        fator_normalizado = (previsao_onda[mask3] - tamanho_ideal) / (tamanho_maximo - tamanho_ideal)
        score[mask3] = np.cos(fator_normalizado * np.pi / 2)

    # --- Seção 4: Onda maior que o limite máximo (Muito Grande/Perigoso) ---
    # A penalidade é uma RETA que começa em 0 e decresce linearmente.
    mask4 = previsao_onda > tamanho_maximo

    # Caso 1: A faixa "grande" (ideal -> max) tem um tamanho.
    if tamanho_maximo > tamanho_ideal:
        # A inclinação (slope) da reta.
        # Será -1 dividido pela largura da faixa "grande".
        # Ex: Se ideal=2m e max=3m, a inclinação é -1.0. A cada 1m extra, o score cai 1.0.
        slope = -2.0 / (tamanho_maximo - tamanho_ideal)

        # Calcula o score usando a equação da reta: y = m * (x - x_inicial)
        score_linear = slope * (previsao_onda[mask4] - tamanho_maximo)

        # Trava o score em -1. Qualquer onda muito grande recebe a penalidade máxima.
        score[mask4] = np.maximum(-1.0, score_linear)

    # Caso 2: Ideal e Máximo são o mesmo valor. Qualquer onda acima recebe penalidade máxima.
    elif tamanho_maximo == tamanho_ideal and tamanho_maximo >= 0:
        score[mask4] = -1.0

    # Multiplica por 100 e arredonda
    return np.round(score * 100, 2)

def calcular_score_direcao_onda(previsao_direcao, direcao_ideal):
    """
    Calcula um score para a direção de uma onda, penalizando assimetricamente.

    Args:
        previsao_direcao (float ou array-like): A direção da onda prevista em graus.
        direcao_ideal (float): A direção ideal da onda (score = 1.0).

    Returns:
        float ou array-like: O score calculado (entre 0 e 1).
    """
    
    previsao_direcao = np.asarray(previsao_direcao, dtype=float)
    direcao_ideal = float(direcao_ideal) # Converter para float
    
    # Calcula a diferença angular
    diferenca = np.abs(previsao_direcao - direcao_ideal) % 360
    diferenca = np.minimum(diferenca, 360 - diferenca)  # Considera o menor ângulo

    # Define o score
    score = np.exp(-diferenca**2 / (45**2))  # Penaliza diferenças maiores que 45 graus

    score = score * 100
    score = np.round(score, 2)

    return score

def calcular_score_periodo_onda(previsao_periodo, periodo_ideal):

    """
    Calcula um score para o período das ondas, penalizando simetricamente.

    Args:
        previsao_periodo (float ou array-like): O período da onda previsto.
        periodo_ideal (float): O período ideal da onda (score = 1.0).

    Returns:
        float ou array-like: O score calculado (entre 0 e 1).
    """
    
    previsao_periodo = np.asarray(previsao_periodo, dtype=float)
    periodo_ideal = float(periodo_ideal) # Converter para float
    score = np.exp(-((previsao_periodo - periodo_ideal) ** 2) / (periodo_ideal + 1e-6)) # Adicionado 1e-6 para evitar divisão por zero

    score = score * 100
    score = np.round(score, 2)

    return score

def calcular_impacto_swell_secundario(
    previsao_swell_secundario_tamanho,
    previsao_swell_secundario_periodo,
    previsao_swell_secundario_direcao,
    previsao_onda_tamanho,
    previsao_onda_periodo,
    previsao_onda_direcao
):
    """
    Calcula o impacto do swell secundário, retornando um valor entre -1 e 1.

    -1: Impacto extremamente negativo (ex: cross swell forte).
     0: Impacto neutro ou insignificante.
    +1: Impacto positivo (ex: swell de enchimento que ajuda a formar picos).
    """
    # --- 1. Score da Direção (o mais importante) ---
    # Usamos o cosseno da diferença de ângulo.
    # Se a diferença é 0°, cos(0) = 1 (alinhamento perfeito, positivo).
    # Se a diferença é 90° (cross swell), cos(90) = 0 (neutro, mas vamos penalizar).
    # Se a diferença é 180°, cos(180) = -1 (swell oposto, muito negativo).
    diferenca_direcao = np.abs(previsao_swell_secundario_direcao - previsao_onda_direcao)
    diferenca_direcao = min(diferenca_direcao, 360 - diferenca_direcao)
    
    # Mapeamos a diferença para uma escala de -1 a 1. Acima de 90° a penalidade é máxima.
    if diferenca_direcao > 90:
        score_direcao = -1.0
    else:
        # Cosseno cria uma curva suave de penalidade.
        score_direcao = np.cos(np.deg2rad(diferenca_direcao))

    # --- 2. Score do Tamanho (relação entre os swells) ---
    # Evita divisão por zero se o swell principal for flat.
    if previsao_onda_tamanho == 0:
        return 0 # Sem swell principal, o secundário não tem impacto.
        
    ratio_tamanho = previsao_swell_secundario_tamanho / previsao_onda_tamanho
    
    # Um swell secundário ideal tem cerca de 30-60% do tamanho do principal.
    # Se for muito grande (>120%), começa a atrapalhar. Se for muito pequeno (<10%), é irrelevante.
    # Usamos uma curva gaussiana centrada em 0.45 (45%).
    score_tamanho = np.exp(-((ratio_tamanho - 0.45)**2) / (0.5**2))
    
    # Penaliza se o swell secundário for muito maior que o principal
    if ratio_tamanho > 1.2:
      score_tamanho *= -1 * (ratio_tamanho - 1.2)


    # --- 3. Score do Período (similaridade) ---
    if previsao_onda_periodo == 0:
        return 0

    ratio_periodo = previsao_swell_secundario_periodo / previsao_onda_periodo
    # Períodos próximos são melhores. Usamos uma curva gaussiana centrada em 1.0 (períodos iguais).
    score_periodo = np.exp(-((ratio_periodo - 1.0)**2) / (0.8**2))

    # --- 4. Cálculo do Impacto Final (Média Ponderada) ---
    # A direção tem o maior peso.
    peso_direcao = 0.60
    peso_tamanho = 0.20
    peso_periodo = 0.20
    
    # O score de direção já está entre -1 e 1. Os outros estão entre 0 e 1.
    # Vamos normalizar o impacto final para garantir que ele fique entre -1 e 1.
    impacto_final = (score_direcao * peso_direcao) + \
                    (score_tamanho * peso_tamanho) + \
                    (score_periodo * peso_periodo)

    # Garante que o resultado final esteja estritamente entre -1 e 1.
    return np.clip(impacto_final, -1.0, 1.0)

def calcular_score_onda(
    # Parâmetros da Previsão Principal
    previsao_tamanho,
    previsao_direcao,
    previsao_periodo,
    
    # Preferências do Usuário
    tamanho_minimo,
    tamanho_ideal,
    tamanho_maximo,
    direcao_ideal,
    periodo_ideal,
    
    # Parâmetros da Previsão do Swell Secundário (opcional)
    previsao_sec_tamanho=0,
    previsao_sec_direcao=0,
    previsao_sec_periodo=0
):
    """
    Calcula o score final e consolidado da condição do mar para o surf.

    A lógica é:
    1. Calcula o score do tamanho da onda. Se for negativo, a condição é ruim e retornamos o score de tamanho.
    2. Se o tamanho for bom, calcula os scores de direção e período.
    3. Combina os três scores em um "score base" através de uma média ponderada.
    4. Calcula o impacto do swell secundário.
    5. Aplica o impacto como bônus (até +10%) ou penalidade (até -20%) sobre o score base.
    """
    
    # Etapa 1: Calcular o score do tamanho da onda
    score_tamanho = calcular_score_tamanho_onda(previsao_tamanho, tamanho_minimo, tamanho_ideal, tamanho_maximo)

    # Etapa 2: Regra de ouro - se o tamanho não é surfável, nada mais importa.
    if score_tamanho < 0:
        return score_tamanho

    # Etapa 3: Se o tamanho é surfável, calcular os outros scores.
    score_direcao = calcular_score_direcao_onda(previsao_direcao, direcao_ideal)
    score_periodo = calcular_score_periodo_onda(previsao_periodo, periodo_ideal)
    
    # Etapa 4: Calcular o "Score Base" com média ponderada (todos os scores estão em escala de 0-100 agora)
    # O tamanho continua sendo o mais importante, seguido pelo período.
    peso_tamanho = 0.50
    peso_periodo = 0.30
    peso_direcao = 0.20
    
    score_base = (score_tamanho * peso_tamanho) + \
                 (score_periodo * peso_periodo) + \
                 (score_direcao * peso_direcao)

    # Etapa 5: Calcular e aplicar o impacto do swell secundário, se houver.
    score_final = score_base
    if previsao_sec_tamanho > 0 and previsao_sec_periodo > 0:
        impacto_secundario = calcular_impacto_swell_secundario(
            previsao_sec_tamanho, previsao_sec_periodo, previsao_sec_direcao,
            previsao_tamanho, previsao_periodo, previsao_direcao
        )
        
        modificador = 0.0
        if impacto_secundario > 0:
            # Bônus máximo de 10%
            modificador = impacto_secundario * 0.10 
        else: # impacto_secundario <= 0
            # Penalidade máxima de 20%
            modificador = impacto_secundario * 0.20

        score_final = score_base * (1 + modificador)
        
    # Etapa 6: Garantir que o score final não ultrapasse 100 e arredondar.
    return np.round(np.clip(score_final, -100, 100), 2)
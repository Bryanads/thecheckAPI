# Documentação TheCheck V2

## Lógica e Fórmulas de Cálculo de Score

O `overall_score` é o coração do TheCheck. Ele traduz uma grande quantidade de dados complexos de previsão em um único número (0-100) que responde à pergunta do surfista: "A condição está boa para mim?". O cálculo é uma média ponderada de quatro componentes principais.

**Fórmula do Score Geral:**

`overall_score = (wave_score * 0.50) + (wind_score * 0.33) + (tide_score * 0.15) + (temperature_score * 0.02)`

| Componente | Peso Final |
| :--- | :--- |
| **Score de Onda/Swell** | **50%** |
| **Score de Vento** | **33%** |
| **Score de Maré** | **15%** |
| **Score de Temperatura** | **2%** |

---

### 3.1 Score de Onda/Swell (Peso: 50%)

Avalia a qualidade da ondulação, sendo o fator mais importante. É calculado em um processo de múltiplas etapas para garantir precisão.

**Fórmula Final:** `wave_score = (Score Base) * (Fator de Penalidade por Inconsistência) * (Fator Modificador de Swell Secundário)`

#### 3.1.1 Cálculo do Score Base

Representa a qualidade "pura" do swell primário. É uma média ponderada de três sub-scores.

**Fórmula:** `Score Base = (ScoreTamanho * 0.70) + (ScorePeríodo * 0.15) + (ScoreDireção * 0.15)`

* **Sub-score de Tamanho do Swell (Peso: 70%)**
    * **Entradas:** `swell_height_sg` (previsão), `ideal_swell_height` e `max_swell_height` (preferências do usuário).
    * **Lógica:** Utiliza uma curva de pontuação suave. O score é **100** quando a altura da previsão é igual à altura ideal do usuário. A pontuação diminui à medida que a altura se afasta do ideal, chegando a **0** na `max_swell_height`. Acima do máximo, o score se torna negativo. Não há um limite mínimo explícito; a própria curva penaliza ondas pequenas com scores baixos naturalmente.

* **Sub-score de Período do Swell (Peso: 15%)**
    * **Entradas:** `swell_period_sg` (previsão), `surf_level` (perfil do usuário).
    * **Lógica:** O sistema infere um `periodo_ideal` com base no nível do surfista para simplificar a experiência do usuário.
        * `iniciante`: Pico de score em períodos mais baixos (ex: 8s).
        * `intermediario`: Pico de score em períodos médios (ex: 11s).
        * `avancado`: Pico de score em períodos mais altos (ex: 14s).
    * A pontuação é calculada usando uma curva de sino em torno do `periodo_ideal` inferido.

* **Sub-score de Direção do Swell (Peso: 15%)**
    * **Entradas:** `swell_direction_sg` (previsão), `ideal_swell_direction` (vetor da tabela `spots`).
    * **Lógica:** O sistema calcula a diferença angular entre a direção prevista e **cada uma** das direções ideais do pico. A **menor diferença** encontrada é usada para calcular o score. Quanto menor a diferença, maior a pontuação.

#### 3.1.2 Fatores de Ajuste

* **Penalidade por Inconsistência (Mar Mexido)**
    * **Lógica:** Compara a altura total da onda com a altura do swell (`ratio = wave_height_sg / swell_height_sg`) para medir a quantidade de marola de vento.
    * Um `ratio` próximo de 1.0 não tem penalidade. Conforme o `ratio` aumenta, uma penalidade de até **60%** é aplicada ao `Score Base`.

* **Modificador de Swell Secundário**
    * **Lógica:** Analisa o swell secundário, principalmente sua direção em relação ao primário.
    * Um swell secundário alinhado pode aplicar um pequeno **bônus** (ex: +10%).
    * Um swell secundário com direção muito diferente (cross swell) aplica uma **penalidade** significativa (ex: -30%). A lógica exata se baseia na função `calcular_impacto_swell_secundario`.

---

### 3.2 Score de Vento (Peso: 33%)

Avalia como o vento afeta a formação e a superfície das ondas.

**Lógica de Cálculo:**
Baseado na função `calcular_score_vento`.
* **Entradas:** `wind_speed_sg`, `wind_dir_sg` (previsão), `max_wind_speed` (preferências do usuário), `ideal_wind_direction` (vetor da tabela `spots`).
* **Funcionamento:** A lógica diferencia o tratamento para vento terral (direção ideal) e maral/lateral.
    * **Se Terral:** A pontuação é alta para ventos fracos a moderados, atingindo o pico e depois decaindo até o `max_wind_speed`.
    * **Se Maral/Lateral:** A pontuação já começa mais baixa e decai mais rapidamente até o `max_wind_speed`.
    * Acima do `max_wind_speed`, o score se torna negativo.

---

### 3.3 Score de Maré (Peso: 15%)

Avalia se a maré está no ponto certo para a bancada do pico funcionar.

**Lógica de Cálculo:**
Adaptado da função `calcular_score_mare`.
* **Entradas:** `sea_level_sg`, `tide_type` (previsão), `ideal_sea_level`, `ideal_tide_flow` (vetor da tabela `spots`).
* **Funcionamento:**
    * **Score de Altura:** Calcula um score baseado na proximidade entre o `sea_level_sg` previsto e o `ideal_sea_level` do pico.
    * **Ajuste pelo Fluxo:** Se o `tide_type` previsto não estiver contido no vetor `ideal_tide_flow` do pico, uma penalidade é aplicada ao score da altura.

---

### 3.4 Score de Temperatura (Peso: 2%)

Fator de conforto que ajusta a qualidade geral da experiência.

**Lógica de Cálculo:**
Baseado nas funções em `temperature_score.py`.
* **Entradas:** `water_temperature_sg`, `air_temperature_sg` (previsão), `ideal_water_temperature`, `ideal_air_temperature` (preferências do usuário).
* **Funcionamento:**
    * Dois scores independentes são calculados para a água e o ar, usando uma curva de sino em torno da temperatura ideal de cada um.
    * O `temperature_score` final, usado na média ponderada, é a **média simples dos dois scores** (`(score_agua + score_ar) / 2`).
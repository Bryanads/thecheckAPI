# Documentação TheCheck V2 

Este documento descreve a arquitetura e as especificações técnicas para a segunda versão do aplicativo TheCheck.

## Arquitetura da API (Endpoints)

A API terá uma separação estrita de responsabilidades. A autenticação será gerenciada via tokens JWT do Supabase, enviados no cabeçalho `Authorization: Bearer <SUPABASE_JWT>`.

### Recurso: `/profile`

Gerencia o perfil do usuário autenticado.

| Método | Endpoint | Protegido | Descrição |
| :--- | :--- | :--- | :--- |
| `GET` | `/profile` | **Sim** | Retorna o perfil completo do usuário autenticado. |
| `PUT` | `/profile` | **Sim** | Atualiza o perfil do usuário autenticado. |



### Recurso: `/spots`

Fornece informações sobre os picos de surf.

| Método | Endpoint | Protegido | Descrição |
| :--- | :--- | :--- | :--- |
| `GET` | `/spots` | Não | Retorna uma lista de picos, com suporte a filtros de busca e geolocalização. |
| `GET` | `/spots/{spot_id}` | Não | Retorna os detalhes de um pico específico. |



### Recurso: `/preferences`

Gerencia as preferências pessoais de um usuário para um pico.

| Método | Endpoint | Protegido | Descrição |
| :--- | :--- | :--- | :--- |
| `GET` | `/preferences/spot/{spot_id}` | **Sim** | Retorna as preferências do usuário para um pico. Se não existirem, a API retorna um padrão com base no `surf_level`. |
| `PUT` | `/preferences/spot/{spot_id}` | **Sim** | Cria ou atualiza as preferências do usuário para um pico. |



### Recurso: `/presets`

Gerencia os presets de busca do usuário.

| Método | Endpoint | Protegido | Descrição |
| :--- | :--- | :--- | :--- |
| `GET` | `/presets` | **Sim** | Retorna a lista de presets do usuário. |
| `POST` | `/presets` | **Sim** | Cria um novo preset. |
| `PUT` | `/presets/{preset_id}` | **Sim** | Atualiza um preset específico. |
| `DELETE`| `/presets/{preset_id}` | **Sim** | Deleta um preset específico. |


### Recurso: `/forecasts` (A Fonte de Dados Brutos)

Este endpoint é a fonte da verdade para os dados de previsão. Ele **não** retorna nenhum tipo de score ou recomendação.

| Método | Endpoint | Protegido | Descrição |
| :--- | :--- | :--- | :--- |
| `GET` | `/forecasts/spot/{spot_id}` | Não | Retorna a previsão bruta e detalhada, hora a hora, para os próximos 7 dias para um `spot_id` específico. |

**Exemplo de Resposta de `GET /forecasts/spot/{spot_id}`:**

```json
{
  "spot_id": 5,
  "spot_name": "Arpoador",
  "daily_forecasts": [
    {
      "date": "2025-09-01",
      "hourly_data": [
        {
          "timestamp_utc": "2025-09-01T08:00:00Z",
          "wave_height_sg": 1.2,
          "swell_height_sg": 1.1,
          "swell_period_sg": 12.5,
          "wind_speed_sg": 3.4
          // ... todos os outros dados brutos, sem o objeto "scores"
        },
        { ... } // Próxima hora
      ]
    },
    { ... } // Próximo dia
  ]
}
```


### Recurso: `/recommendations` 

Este endpoint consome os dados da previsão internamente, cruza com as preferências do usuário e retorna uma lista classificada dos melhores momentos para surfar.

| Método | Endpoint | Protegido | Descrição |
| :--- | :--- | :--- | :--- |
| `POST` | `/recommendations` | **Sim** | Recebe um conjunto de critérios e um limite, e retorna uma lista classificada das **melhores sessões de surf** encontradas. |

**Nota de Implementação:** A resposta deste endpoint contém `spot_id` e `timestamp_utc`. O frontend **deve usar estes dados para construir a rota de navegação** para a tela de previsão detalhada, garantindo que o backend permaneça desacoplado da estrutura de rotas do cliente.

**Exemplo de Corpo para `POST /recommendations`:**

```json
{
  "spot_ids": [1, 5, 12],
  "day_selection": {
    "type": "offsets", 
    "values": [0, 1] 
  },
  "time_window": {
    "start": "06:00:00",
    "end": "18:00:00"
  },
  "limit": 5
}
```

**Exemplo de Resposta de `POST /recommendations`:**

```json
[
  {
    "spot_id": 5,
    "spot_name": "Arpoador",
    "timestamp_utc": "2025-09-01T12:00:00Z",
    "overall_score": 94.5,
    "detailed_scores": {
        "wave_score": 98.0,
        "wind_score": 95.0,
        "tide_score": 89.0,
        "water_temperature_score": 92.0,
        "air_temperature_score": 88.0
    }
  }
]
```

-----

# Documentação TheCheck V2 - Data Base

Este documento descreve a arquitetura e as especificações técnicas para a segunda versão do aplicativo TheCheck.

## Schema do Banco de Dados (PostgreSQL)

A seguir, a definição de todas as tabelas do banco de dados, incluindo os scripts SQL para a criação. A arquitetura foi projetada para ser normalizada, eficiente e escalável.

### Tabela: `profiles`

Armazena os dados de perfil de cada usuário, sendo uma extensão da tabela `auth.users` do Supabase. Um perfil é criado automaticamente via `TRIGGER` quando um novo usuário se cadastra.

| Nome da Coluna | Tipo de Dado | Restrições/Notas |
| :--- | :--- | :--- |
| `id` | `UUID` | Chave Primária, Referencia `auth.users.id`, `ON DELETE CASCADE` |
| `name` | `TEXT` | `NOT NULL` |
| `email` | `TEXT` | `UNIQUE`, `NOT NULL` |
| `location` | `TEXT` | Opcional, ex: "Rio de Janeiro, RJ" |
| `bio` | `TEXT` | Opcional, descrição do usuário |
| `surf_level` | `TEXT` | `DEFAULT 'intermediario'` |
| `stance` | `TEXT` | `DEFAULT 'Regular'` |
| `created_at` | `TIMESTAMPTZ` | `DEFAULT now()` |
| `updated_at` | `TIMESTAMPTZ` | `DEFAULT now()` |

**Schema SQL:**

```sql
CREATE TABLE public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    location TEXT,
    bio TEXT,
    surf_level TEXT DEFAULT 'intermediario',
    stance TEXT DEFAULT 'Regular',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
```


### Tabela: `spots`

Armazena as características físicas e geográficas de cada pico de surf. Esta tabela é a fonte de "inteligência" sobre as condições ideais de cada local.

| Nome da Coluna | Tipo de Dado | Restrições/Notas |
| :--- | :--- | :--- |
| `spot_id` | `SERIAL` | Chave Primária |
| `name` | `TEXT` | `UNIQUE`, `NOT NULL` |
| `latitude` | `NUMERIC(10, 7)` | `NOT NULL` |
| `longitude` | `NUMERIC(10, 7)` | `NOT NULL` |
| `timezone` | `TEXT` | `NOT NULL`, ex: "America/Sao\_Paulo" |
| `bottom_type` | `TEXT` | Opcional, ex: 'areia', 'pedra', 'coral' |
| `break_type` | `TEXT` | Opcional, ex: 'beach break', 'point break' |
| `difficulty_level`| `TEXT` | Opcional, ex: 'iniciante', 'todos os niveis' |
| `ideal_swell_direction` | `NUMERIC(5, 2)[]` | Vetor de direções (ex: `{180, 157.5}` para S e SSE) |
| `ideal_wind_direction` | `NUMERIC(5, 2)[]` | Vetor de direções do vento terral |
| `ideal_sea_level` | `NUMERIC(4, 2)` | Altura ideal da maré (em metros) |
| `ideal_tide_flow` | `TEXT[]` | Vetor de fases da maré (ex: `{'subindo', 'descendo'}`) |

**Schema SQL:**

```sql
CREATE TABLE public.spots (
    spot_id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    latitude NUMERIC(10, 7) NOT NULL,
    longitude NUMERIC(10, 7) NOT NULL,
    timezone TEXT NOT NULL,
    bottom_type TEXT,
    break_type TEXT,
    difficulty_level TEXT,
    ideal_swell_direction NUMERIC(5, 2)[],
    ideal_wind_direction NUMERIC(5, 2)[],
    ideal_sea_level NUMERIC(4, 2),
    ideal_tide_flow TEXT[]
);
```

### Tabela: `user_spot_preferences`

Armazena as preferências **pessoais** de um usuário para um pico específico. É uma tabela de ligação que permite a personalização do score.

| Nome da Coluna | Tipo de Dado | Nota |
| :--- | :--- | :--- |
| `preference_id` | `SERIAL` | Chave Primária |
| `user_id` | `UUID` | FK para `profiles.id` |
| `spot_id` | `INT` | FK para `spots.spot_id` |
| `ideal_swell_height` | `NUMERIC(4, 2)` | Altura de swell para o dia perfeito. |
| `max_swell_height` | `NUMERIC(4, 2)` | O limite máximo de swell que ele encara. |
| `max_wind_speed` | `NUMERIC(4, 2)` | Velocidade máxima de vento que ele aceita. |
| `ideal_water_temperature` | `NUMERIC(4, 2)`| Temperatura da água ideal para o usuário. |
| `ideal_air_temperature` | `NUMERIC(4, 2)` | Temperatura do ar ideal para o usuário. |
| `is_active` | `BOOLEAN` | `DEFAULT true` |

**Schema SQL:**

```sql
CREATE TABLE public.user_spot_preferences (
    preference_id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    spot_id INT NOT NULL REFERENCES public.spots(spot_id) ON DELETE CASCADE,
    ideal_swell_height NUMERIC(4, 2),
    max_swell_height NUMERIC(4, 2),
    max_wind_speed NUMERIC(4, 2),
    ideal_water_temperature NUMERIC(4, 2),
    ideal_air_temperature NUMERIC(4, 2),
    is_active BOOLEAN DEFAULT true,
    UNIQUE (user_id, spot_id)
);
```

### Tabela: `presets`

Armazena as configurações de busca salvas por um usuário, permitindo consultas rápidas e personalizadas.

| Nome da Coluna | Tipo de Dado | Nota |
| :--- | :--- | :--- |
| `preset_id` | `SERIAL` | Chave Primária |
| `user_id` | `UUID` | FK para `profiles.id` |
| `name` | `TEXT` | "Check diário", "Fim de semana" |
| `spot_ids` | `INTEGER[]` | Vetor de IDs de spots (ex: `{1, 5, 12}`) |
| `start_time` | `TIME` | Hora de início da busca (ex: '06:00:00') |
| `end_time` | `TIME` | Hora de fim da busca (ex: '18:00:00') |
| `day_selection_type` | `TEXT` | 'weekdays' ou 'offsets' |
| `day_selection_values`| `INTEGER[]`| Vetor com os dias da semana (0-6) ou offsets (0-6) |
| `is_default` | `BOOLEAN` | `DEFAULT false` |

**Schema SQL:**

```sql
CREATE TABLE public.presets (
    preset_id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    spot_ids INTEGER[] NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    day_selection_type TEXT NOT NULL,
    day_selection_values INTEGER[] NOT NULL,
    is_default BOOLEAN DEFAULT false
);
```

### Tabela: `forecasts`

Armazena os dados horários de previsão do tempo e do mar para cada spot. Esta é a tabela mais consultada e atualizada.

| Nome da Coluna | Tipo de Dado | Nota |
| :--- | :--- | :--- |
| `forecast_id` | `SERIAL` | Chave Primária |
| `spot_id` | `INTEGER` | `NOT NULL`, FK para `spots.spot_id` |
| `timestamp_utc` | `TIMESTAMPTZ` | `NOT NULL`, Data e hora da previsão |
| `wave_height_sg` | `NUMERIC(5, 2)` | |
| `wave_direction_sg` | `NUMERIC(6, 2)` | |
| `wave_period_sg` | `NUMERIC(5, 2)` | |
| `swell_height_sg` | `NUMERIC(5, 2)` | |
| `swell_direction_sg`| `NUMERIC(6, 2)` | |
| `swell_period_sg` | `NUMERIC(5, 2)` | |
| `secondary_swell_height_sg`| `NUMERIC(5, 2)` | |
| `secondary_swell_direction_sg`| `NUMERIC(6, 2)`| |
| `secondary_swell_period_sg` | `NUMERIC(5, 2)` | |
| `wind_speed_sg` | `NUMERIC(5, 2)` | |
| `wind_direction_sg` | `NUMERIC(6, 2)` | |
| `water_temperature_sg`| `NUMERIC(5, 2)` | |
| `air_temperature_sg`| `NUMERIC(5, 2)` | |
| `current_speed_sg` | `NUMERIC(5, 2)` | |
| `current_direction_sg`| `NUMERIC(6, 2)` | |
| `sea_level_sg` | `NUMERIC(5, 2)` | |
| `tide_type` | `VARCHAR(10)` | 'rising', 'falling', 'high', 'low' |
| `last_modified_at`| `TIMESTAMPTZ` | `DEFAULT now()` |
| `UNIQUE` | `(spot_id, timestamp_utc)` | Garante que não haja entradas duplicadas. |

**Schema SQL:**

```sql
CREATE TABLE public.forecasts (
    forecast_id SERIAL PRIMARY KEY,
    spot_id INTEGER NOT NULL REFERENCES public.spots(spot_id) ON DELETE CASCADE,
    timestamp_utc TIMESTAMPTZ NOT NULL,
    wave_height_sg NUMERIC(5, 2),
    wave_direction_sg NUMERIC(6, 2),
    wave_period_sg NUMERIC(5, 2),
    swell_height_sg NUMERIC(5, 2),
    swell_direction_sg NUMERIC(6, 2),
    swell_period_sg NUMERIC(5, 2),
    secondary_swell_height_sg NUMERIC(5, 2),
    secondary_swell_direction_sg NUMERIC(6, 2),
    secondary_swell_period_sg NUMERIC(5, 2),
    wind_speed_sg NUMERIC(5, 2),
    wind_direction_sg NUMERIC(6, 2),
    water_temperature_sg NUMERIC(5, 2),
    air_temperature_sg NUMERIC(5, 2),
    current_speed_sg NUMERIC(5, 2),
    current_direction_sg NUMERIC(6, 2),
    sea_level_sg NUMERIC(5, 2),
    tide_type VARCHAR(10),
    last_modified_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (spot_id, timestamp_utc)
);
```
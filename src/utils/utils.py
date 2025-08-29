import arrow
import os
import json
import datetime
import decimal

def load_json_data(filename, directory):
    """
    Carrega dados JSON a partir de um arquivo localizado no diretório especificado.
    """
    path = os.path.join(directory, filename)
    if not os.path.exists(path):
        print(f"Arquivo não encontrado: {path}")
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Erro ao carregar JSON de {path}: {e}")
        return None

def save_json_data(data, filename, directory):
    """
    Salva dados em formato JSON no diretório especificado.
    Cria o diretório se ele não existir.
    """
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, filename)
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Erro ao salvar JSON em {path}: {e}")
        raise e

def convert_to_localtime(data, timezone='America/Sao_Paulo'):
    for entry in data:
        try:
            local_time = arrow.get(entry['time']).to(timezone)
            entry['time'] = local_time.isoformat()
        except Exception as e:
            print(f"Erro ao converter horário: {entry.get('time')} | {e}")
    return data

def convert_to_localtime_string(timestamp_str, timezone='America/Sao_Paulo'):
    """Converte um timestamp string UTC para uma string no fuso horário local e formata."""
    if not timestamp_str:
        return ""
    try:
        utc_time = arrow.get(timestamp_str).to('utc')
        local_time = utc_time.to(timezone)
        return local_time.format('YYYY-MM-DD HH:mm:ss ZZZ')
    except Exception as e:
        print(f"Erro ao converter string de horário '{timestamp_str}' para horário local: {e}")
        return ""

def load_config(file_path='config.json'):
    """Carrega as configurações de um arquivo JSON."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Erro: O arquivo de configuração '{file_path}' não foi encontrado.")
        return None
    except json.JSONDecodeError:
        print(f"Erro: O arquivo '{file_path}' não é um JSON válido.")
        return None
    except Exception as e:
        print(f"Erro ao carregar o arquivo de configuração '{file_path}': {e}")
        return None

def save_config(config_data, file_path='config.json'):
    """Salva as configurações em um arquivo JSON."""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=4)
        print(f"Configuração salva em '{file_path}'.")
    except Exception as e:
        print(f"Erro ao salvar o arquivo de configuração '{file_path}': {e}")

def get_cardinal_direction(degrees):
    """
    Converts degrees (0-360) to a cardinal or intercardinal direction.
    Handles decimal.Decimal input by converting to float.
    """
    if degrees is None:
        return "N/A"
    
    # Adicionar esta linha para garantir que 'degrees' seja um float
    if isinstance(degrees, decimal.Decimal):
        degrees = float(degrees)

    directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                  "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    
    # Adiciona 11.25 para ajustar o ponto de partida (N é de 348.75 a 11.25)
    index = int((degrees + 11.25) / 22.5) % 16
    return directions[index]

def cardinal_to_degrees(cardinal_direction_str):
    """Converts a cardinal direction string to its numerical degree representation (0-360)."""
    if cardinal_direction_str is None:
        return None
    mapping = {
        'N': 0, 'NNE': 22.5, 'NE': 45, 'ENE': 67.5,
        'E': 90, 'ESE': 112.5, 'SE': 135, 'SSE': 157.5,
        'S': 180, 'SSW': 202.5, 'SW': 225, 'WSW': 247.5,
        'W': 270, 'WNW': 292.5, 'NW': 315, 'NNW': 337.5
    }
    return mapping.get(cardinal_direction_str.upper(), None)

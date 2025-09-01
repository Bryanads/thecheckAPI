from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import requests # Certifique-se de ter essa biblioteca: pip install requests
from src.core.config import settings

bearer_scheme = HTTPBearer()

# Pega as chaves públicas do Supabase. Elas são cacheadas para performance.
jwks_url = f"{settings.SUPABASE_URL}/auth/v1/jwks"
jwks = requests.get(jwks_url).json()

async def get_current_user_id(creds: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> str:
    """
    Decodifica o token JWT (formato Bearer) do Supabase usando o método JWKS moderno.
    """
    token = creds.credentials
    try:
        # Pega o cabeçalho do token sem verificar a assinatura ainda
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        if not kid:
            raise HTTPException(status_code=401, detail="Cabeçalho 'kid' não encontrado no token.")

        # Encontra a chave de assinatura correta no JWKS
        signing_key = None
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                signing_key = key
                break
        
        if not signing_key:
             raise HTTPException(status_code=401, detail="Chave de assinatura não encontrada para o 'kid' do token.")

        # Agora, decodifica o token usando a chave pública correta
        payload = jwt.decode(
            token,
            jwt.algorithms.RSAAlgorithm.from_jwk(signing_key),
            algorithms=["RS256"],
            audience="authenticated" # Verifica se o token é para um usuário autenticado
        )
        
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Token inválido: user_id não encontrado.")
            
        return user_id

    except jwt.ExpiredSignatureError:
         raise HTTPException(status_code=401, detail="Token expirado.")
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=401, detail=f"Não foi possível validar as credenciais do token: {e}")
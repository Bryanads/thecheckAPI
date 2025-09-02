import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.core.config import settings

bearer_scheme = HTTPBearer()

async def get_current_user_id(creds: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> str:
    """
    Decodifica o token JWT usando o segredo compartilhado.
    """
    token = creds.credentials
    try:
        # Decodifica o token usando o segredo JWT
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated"
        )
        
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido: user_id não encontrado.")
            
        return user_id

    except jwt.ExpiredSignatureError:
         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expirado.")
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Não foi possível validar as credenciais do token: {e}")
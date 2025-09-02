from fastapi import APIRouter, HTTPException
from typing import List
from src.core.schemas import Spot  # Importa o schema que criamos
from src.db import queries         # Importa nosso módulo de queries

router = APIRouter(
    prefix="/spots",
    tags=["Spots"]
)

@router.get("/", response_model=List[Spot])
async def get_all_spots_endpoint():
    """
    Retorna uma lista de todos os picos de surf disponíveis.
    """
    spots = await queries.get_all_spots()
    if not spots:
        # Se não houver spots, podemos retornar uma lista vazia ou um erro.
        # Por enquanto, uma lista vazia está ótimo.
        return []
    return spots
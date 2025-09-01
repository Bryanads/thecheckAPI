import asyncpg
from src.core.config import settings

_pool = None

async def get_db_pool():
    """
    Inicializa e retorna o pool de conexões.
    """
    global _pool
    if _pool is None:
        print("Criando novo pool de conexões...")
        _pool = await asyncpg.create_pool(
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            database=settings.DB_NAME,
            min_size=1,
            max_size=10
        )
        print("Pool de conexões criado com sucesso.")
    return _pool

async def close_db_pool():
    """
    Fecha o pool de conexões para um encerramento limpo.
    """
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        print("Pool de conexões fechado.")

async def get_connection():
    """
    Adquire uma conexão do pool para executar uma query.
    """
    pool = await get_db_pool()
    return await pool.acquire()

async def release_connection(conn):
    """
    Libera uma conexão de volta para o pool após o uso.
    """
    pool = await get_db_pool()
    if pool and conn:
        await pool.release(conn)
from contextlib import asynccontextmanager
from fastapi import FastAPI
from redis.asyncio import Redis
from core.retries import retry

redis_client = Redis(host="redis", port=6379, decode_responses=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await retry(redis_client.ping, name='redis')
    app.state.redis = redis_client
    yield
    await redis_client.close()

import asyncio
import logging

logger = logging.getLogger(__name__)


class RetryError(Exception):
    pass


async def retry(
        fn,
        *,
        retries: int = 10,
        base_delay: float = 0.5,
        max_delay: float = 5.0,
        name: str = "service"
):
    delay = base_delay
    for attempt in range(retries):
        try:
            return await fn()
        except Exception as e:
            logger.warning(f"[{name}] attempt {attempt} failed: {e}")
            await asyncio.sleep(delay)
            delay = min(delay * 2, max_delay)
    raise RetryError(f"{name} failed after {retries} attempts")

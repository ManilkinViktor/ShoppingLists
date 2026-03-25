
import logging
from core.logger import get_queue_handler
import uvicorn
from fastapi import FastAPI

from api.auth import router as auth_router
from api.shopping_lists import router as shopping_lists_router
from api.workspaces import router as workspaces_router
from schemas import rebuild_models


rebuild_models()


app = FastAPI(title='ShoppingLists API')
app.include_router(auth_router)
app.include_router(workspaces_router)
app.include_router(shopping_lists_router)

# --- Ensure root logger uses QueueHandler ---
root_logger = logging.getLogger()
if not any(isinstance(h, logging.handlers.QueueHandler) for h in root_logger.handlers):
    root_logger.addHandler(get_queue_handler())
    root_logger.setLevel(logging.INFO)


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)

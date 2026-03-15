from fastapi import FastAPI
import uvicorn

from api.auth import router as auth_router
from api.shopping_lists import router as shopping_lists_router
from api.workspaces import router as workspaces_router


app = FastAPI(title='ShoppingLists API')
app.include_router(auth_router)
app.include_router(workspaces_router)
app.include_router(shopping_lists_router)

if __name__ == '__main__':
    uvicorn.run(app)

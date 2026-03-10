from fastapi import FastAPI
import uvicorn

from api.auth import router as auth_router
from api.workspaces import router as workspaces_router


app = FastAPI(title='ShoppingLists API')
app.include_router(auth_router)
app.include_router(workspaces_router)

if __name__ == '__main__':
    uvicorn.run(app)
from fastapi import FastAPI
from starlette.responses import RedirectResponse  # Correct import
from .routers import auth, threads  # Import the items router
from fastapi.middleware.cors import CORSMiddleware
from app.config.AppConfig import config

app = FastAPI(title=config.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

#intiailize pinecone



# Your routes and other code here...
app.include_router(auth.router, prefix="/v1/api/auth")
app.include_router(threads.router, prefix="/v1/api/thread")

@app.get("/")
async def get_root():
    return {"Health": "OK"}

#enables automated documentation
@app.get("/redoc")
async def get_redoc():
    return RedirectResponse(url="/redoc")


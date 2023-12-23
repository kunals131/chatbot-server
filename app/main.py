from fastapi import FastAPI
from starlette.responses import RedirectResponse  # Correct import
from .routers import auth  # Import the items router
from fastapi.middleware.cors import CORSMiddleware
from config.AppConfig import config


app = FastAPI(title=config.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Your routes and other code here...
app.include_router(auth.router)


#enables automated documentation
@app.get("/redoc")
async def get_redoc():
    return RedirectResponse(url="/redoc")


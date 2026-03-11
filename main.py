from fastapi import FastAPI
from supercell_routes import app as supercell_app
from custom_routes import router as custom_router

app = supercell_app

app.include_router(custom_router)

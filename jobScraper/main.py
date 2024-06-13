# FastAPI RestAPI for database object manipulation
# .
# |- main.py > RestAPI application
# | 
# |- routers > API routes/methods declaration
# |   |-manufacturer_router.py 
# |   |-panel_router.py
# |   |
# |   |-models > data models
# |      |-manufacturer.py
# |      |-panel.py

# https://www.mongodb.com/languages/python/pymongo-tutorial
# python3 -m venv env-pymongo-fastapi-crud
# source env-pymongo-fastapi-crud/bin/activate
# python -m pip install 'fastapi[all]' 'pymongo[srv]' python-dotenv
# python -m uvicorn main:app --reload

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import dotenv_values
from pymongo import MongoClient

#from routers import *
#import routers

from routers.job_router import router as job_router

config = dotenv_values(".env")
MongoClient
app = FastAPI()

origins = [
    "http://192.168.99:3000",
    "http://localhost:3000",
    "http://192.168.98:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins = origins,
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"],
)

@app.on_event("startup")
def startup_db_client():
    app.mongodb_client = MongoClient(config["CONN_URI"])
    app.database = app.mongodb_client[config["DB_NAME"]]
    print("Connected to the MongoDB database!")

@app.on_event("shutdown")
def shutdown_db_client():
    app.mongodb_client.close()

app.include_router(job_router, tags=["jobs"], prefix=f"/jobs")

@app.get("/")
async def root():
    return {"message": "Welcome to the PyMongo tuto!"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", reload=True)

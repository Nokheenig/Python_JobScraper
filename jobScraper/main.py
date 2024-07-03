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
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, validator, ValidationError
from typing import Union
#from fastapi import APIRouter, Body, Request, Response, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from dotenv import dotenv_values
from pymongo import MongoClient

import os
from definitions import ROOT_DIR
import logging as log
log.basicConfig(filename=os.path.join(ROOT_DIR,"logs","api.log"), encoding='utf-8', filemode='a', format='%(asctime)s-%(levelname)s:%(message)s', level=log.DEBUG)

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
    "http://192.168.99:3000/*",
    "http://localhost:3000/*",
    "http://192.168.98:3000/*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],#origins,
    #allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"],
    expose_headers = ["*"]
)

async def http422_error_handler(
    _: Request, exc: Union[RequestValidationError, ValidationError]) -> JSONResponse:
    log.debug(f"http422_error_handler - Exception errors: {exc.errors()}")
    log.debug(f"http422_error_handler - Exception: {exc}")
    return JSONResponse(
        {"errors": exc.errors()}, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
    )

app.add_exception_handler(ValidationError, http422_error_handler)
app.add_exception_handler(RequestValidationError, http422_error_handler)

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

from fastapi import APIRouter, Body, Request, Response, HTTPException, status
from fastapi.encoders import jsonable_encoder
from typing import List
from pydantic import BaseModel, Field
from typing import Annotated
import os
import re
from definitions import ROOT_DIR
import logging as log
log.basicConfig(filename=os.path.join(ROOT_DIR,"logs","test.log"), encoding='utf-8', filemode='a', format='%(asctime)s-%(levelname)s:%(message)s', level=log.DEBUG)
from pymongo import ASCENDING, DESCENDING


from .models.job import Job as objectModel
from .models.job import JobUpdate as objectUpdateModel
objectName = "job"
routerName = f"{objectName}_router"
#exec(routerName = APIRouter())
router = APIRouter()

#
@router.post("/", response_description=f"Creates a new {objectName} in database", status_code=status.HTTP_201_CREATED)#, response_model=objectModel)
def create_object(request: Request, obj: objectModel = Body(...)):
    obj = jsonable_encoder(obj)
    projection = {
        "_id": 1,
        "platform": 1,
        "company": 1,
        "title": 1,
    }
    new_obj = request.app.database[f"{objectName}s"].insert_one(obj)
    created_obj = request.app.database[f"{objectName}s"].find_one(
        {"_id": new_obj.inserted_id},
        projection
    )

    return created_obj

#

@router.get("/", response_description=f"Returns all {objectName}s in the database (defaults: page=1, perPage=2)")#, response_model=List[objectModel])
def list_objects(request: Request, page:int=1, perPage:int=25, 
                 status: str = "Null,New,Open_ReferalStage,Open_ReadyToApply,OnGoing_SelectedForApplication"
                 ):

    status = re.sub("[\{\}:01]", "-", status)
    selectedStatus = status.split(",")
    nullStatus = "Null" in selectedStatus
    if nullStatus: 
        selectedStatus.remove("Null")
        selectedStatus.append(None)
    log.debug(selectedStatus)

    col = request.app.database[f"{objectName}s"]
    query = {"status": {"$in": selectedStatus}}
    projection = {}
    objects = list(col.find(query, projection, limit=perPage, skip=((page-1)*perPage)))
    docCount = col.count_documents(query)

    return {
        "documents_count": docCount,
        "page": page,
        "perPage":perPage,
        "data": objects
    }

#panels = [panel for panel in request.app.database[f"{objectName}s"].find({},projection)]

@router.get("/list", response_description=f"Returns a summary list of all {objectName}s in database")
def sumlist_objects(request: Request, page:int=1, perPage:int=100):
    col = request.app.database[f"{objectName}s"]
    query = { }
    projection = {
        "_id": 1,
        "title": 1,
        "company": 1,
        "country": 1,
        "city": 1,
        "applyUrl": 1
    }

    objects = [obj for obj in col.find(query,projection)]
    #objDict = {f"{panel['manufacturer']}_{panel['model']}": panel for panel in panels}
    docCount = col.count_documents(query)

    return {
        "documents_count": docCount,
        "page": page,
        "perPage":perPage,
        "data": objects
    }

@router.get("/scraped-urls", response_description=f"Returns a summary list of all {objectName}s in database")
def sumlist_objects(request: Request):
    query = {
        "manufacturer": "1Soltech"
    }
    projection = {
        "title": 1,
        "company": 1,
        "country": 1,
        "city": 1,
        "url": 1,
        "applyUrl": 1
    }

    objects = [obj for obj in request.app.database[f"{objectName}s"].find({},projection)]
    #objDict = {f"{panel['manufacturer']}_{panel['model']}": panel for panel in panels}
    out = {obj["url"] : None for obj in objects}
    return out
    return objects

@router.get("/{id}", response_description=f"Returns {objectName} with provided id", response_model=objectModel)
def find_object(id: str, request: Request):
    if (obj := request.app.database[f"{objectName}s"].find_one({"_id": id})) is not None:
        return obj
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{objectName.capitalize()} with ID {id} not found")

#
@router.patch("/{id}", response_description=f"Updates {objectName} in database with provided id with provided dictionnary object",)#, response_model=objectModel)
def update_object(id: str, request: Request, obj: objectUpdateModel = Body(...)):
    #obj = {k: v for k, v in obj.dict().items() if v is not None}
    obj = obj.dict(exclude_unset=True)
    if len(obj) >= 1:
        update_result = request.app.database[f"{objectName}s"].update_one(
            {"_id": id}, {"$set": obj}
        )

        if update_result.modified_count == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{objectName.capitalize()} with ID {id} not found")

    if (
        existing_obj := request.app.database[f"{objectName}s"].find_one({"_id": id})
    ) is not None:
        return existing_obj

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{objectName.capitalize()} with ID {id} not found")
"""
"""
#
@router.delete("/{id}", response_description=f"Deletes {objectName} in database with provided id")
def delete_object(id: str, request: Request, response: Response):
    delete_result = request.app.database[f"{objectName}s"].delete_one({"_id": id})

    if delete_result.deleted_count == 1:
        response.status_code = status.HTTP_204_NO_CONTENT
        return response

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{objectName.capitalize()} with ID {id} not found")

@router.get("/stats/applications-count", response_description=f"Returns a summary of daily applications")
def applicationsCount(request: Request):
    col = request.app.database[f"{objectName}s"]
    query = { 
        "applicationDate": {
            "$nin": [None]
        }
     }
    projection = {
        "applicationDate": 1,
    }

    objects = [obj["applicationDate"] for obj in col.find(query,projection)]
    appCount = {}
    for applicationTimestamp in objects:
        day = applicationTimestamp[:applicationTimestamp.find("T")]
        if day not in appCount:
            appCount[day] = 1
        else:
            appCount[day] +=1

    monthly = {}
    for timestamp in appCount:
        month = timestamp[:timestamp.rfind("-")]
        if month not in monthly:
            monthly[month] = appCount[timestamp]
        else:
            monthly[month] += appCount[timestamp]

    yearly = {}
    for timestamp in monthly:
        year = timestamp[:timestamp.rfind("-")]
        if year not in yearly:
            yearly[year] = monthly[timestamp]
        else:
            yearly[year] += monthly[timestamp]

    daily = [f"{k}: {v}" for k,v in appCount.items()]
    monthly = [f"{k}: {v}" for k,v in monthly.items()]
    yearly = [f"{k}: {v}" for k,v in yearly.items()]

    return {
        "yearly": yearly,
        "monthly": monthly,
        "daily": daily
    }
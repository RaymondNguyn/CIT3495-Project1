from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy import create_engine, Column, Integer, Float, DateTime, MetaData, Table, func
from datetime import datetime
import httpx
import os
from typing import Optional
import databases
import mysql.connector
from mysql.connector import Error
import requests

# Database URL with mysql-connector-python
DATABASE_URL = (
    f"mysql+mysqlconnector://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}@"
    f"{os.getenv('MYSQL_HOST')}/{os.getenv('MYSQL_DATABASE')}"
)

# FastAPI app
app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection
database = databases.Database(DATABASE_URL)
metadata = MetaData()

# Data table definition
data_points = Table(
    "data_points",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("min_value", Float),
    Column("max_value", Float),
    Column("avg_value", Float),
    Column("timestamp", DateTime, default=datetime.utcnow),
    Column("user_id", Integer),
)

# Startup and shutdown events
@app.on_event("startup")
async def startup():
    await database.connect()
    engine = create_engine(DATABASE_URL)
    metadata.create_all(engine)  # Creates the modified table

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

# Token grabber3000
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth_service:3000")


# Auth middleware
def verify_token(token: str):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{AUTH_SERVICE_URL}/verify", headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid token")

    return response.json()["user"]

@app.post("/data")
async def create_data_point(value: float, user: dict = Depends(verify_token)):
    return {"message": "Authenticated successfully", "user": user}

# Routes
@app.post("/data")
async def create_data_point(
    min_value: float,
    max_value: float,
    avg_value: float,
    user: dict = Depends(verify_token)
):
    query = data_points.insert().values(
        min_value=min_value,
        max_value=max_value,
        avg_value=avg_value,
        user_id=user["userId"]
    )
    try:
        await database.execute(query)
        return {"message": "Data point created successfully"}
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/data")
async def get_data_points(request: Request, token: Optional[str] = None):
    if token is None:
        token = request.cookies.get("auth_token")
    
    if not token:
        return RedirectResponse(url="http://auth_service:3000")  # Redirect back to login

    user = verify_token(token)
    file_path = os.path.join(os.getcwd(), "static", "index.html")
    return FileResponse(file_path)

# return {"message": "Authenticated successfully", "user": user}
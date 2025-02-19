from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, Float, DateTime, MetaData, Table
from datetime import datetime
import httpx
import os
from typing import Optional
import databases
import mysql.connector
from mysql.connector import Error

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
    Column("value", Float),
    Column("timestamp", DateTime, default=datetime.utcnow),
    Column("user_id", Integer),
)

# Startup and shutdown events
@app.on_event("startup")
async def startup():
    try:
        await database.connect()
        # Create tables
        engine = create_engine(DATABASE_URL)
        metadata.create_all(engine)
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        raise e

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

# Auth middleware
async def verify_token(token: str = Depends(lambda x: x.headers.get("Authorization"))):
    if not token:
        raise HTTPException(status_code=401, detail="No token provided")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{os.getenv('AUTH_SERVICE_URL')}/verify",
            headers={"Authorization": token}
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        return response.json()["user"]

# Routes
@app.post("/data")
async def create_data_point(value: float, user: dict = Depends(verify_token)):
    query = data_points.insert().values(
        value=value,
        user_id=user["userId"]
    )
    try:
        await database.execute(query)
        return {"message": "Data point created successfully"}
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/data")
async def get_data_points(user: dict = Depends(verify_token)):
    query = data_points.select().where(data_points.c.user_id == user["userId"])
    try:
        return await database.fetch_all(query)
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
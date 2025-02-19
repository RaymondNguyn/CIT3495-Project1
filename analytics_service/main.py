# analytics_service/main.py
import asyncio
import os
from sqlalchemy import create_engine, text
from pymongo import MongoClient
import pandas as pd
from datetime import datetime

# Database configurations
MYSQL_URL = (
    f"mysql+mysqlconnector://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}@"
    f"{os.getenv('MYSQL_HOST')}/{os.getenv('MYSQL_DATABASE')}"
)
MONGO_URI = os.getenv('MONGO_URI')

# Initialize database connections
mysql_engine = create_engine(MYSQL_URL)
mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client['analytics']
mongo_collection = mongo_db['statistics']

async def compute_analytics():
    while True:
        try:
            # Read data from MySQL
            with mysql_engine.connect() as connection:
                query = text("SELECT value FROM data_points")
                result = connection.execute(query)
                data = [row[0] for row in result]

            if data:
                # Compute statistics
                df = pd.Series(data)
                stats = {
                    'timestamp': datetime.utcnow(),
                    'count': len(df),
                    'mean': float(df.mean()),
                    'std': float(df.std()) if len(df) > 1 else 0,
                    'min': float(df.min()),
                    'max': float(df.max()),
                    'median': float(df.median())
                }

                # Store in MongoDB
                mongo_collection.insert_one(stats)
                print(f"Analytics computed and stored: {stats}")
            else:
                print("No data available for analysis")

        except Exception as e:
            print(f"Error computing analytics: {e}")

        # Wait for 5 minutes before next computation
        await asyncio.sleep(300)

if __name__ == "__main__":
    try:
        # Test database connections on startup
        mysql_engine.connect()
        mongo_client.server_info()
        print("Database connections successful")
        
        # Run the analytics loop
        loop = asyncio.get_event_loop()
        loop.run_until_complete(compute_analytics())
    except Exception as e:
        print(f"Startup error: {e}")
        raise
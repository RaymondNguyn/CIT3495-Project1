import os
import time
from typing import List, Dict, Optional
import numpy as np
import mysql.connector
from mysql.connector import Error
from pymongo import MongoClient, errors

# Database configurations
MYSQL_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "mysql"),
    "database": os.getenv("MYSQL_DB", "datadb"),
    "user": os.getenv("MYSQL_USER", "user"),
    "password": os.getenv("MYSQL_PASSWORD", "password"),
}

MONGO_URI = os.getenv(
    "MONGO_URI", 
    "mongodb://root:rootpassword@mongodb:27017/admin?authSource=admin&authMechanism=SCRAM-SHA-1"
)

MONGO_DB = "datadb"
MONGO_COLLECTION = "float_statistics"

def get_mysql_connection(retries: int = 5, delay: int = 5) -> Optional[mysql.connector.MySQLConnection]:
    """Establish connection to MySQL with retry logic."""
    for attempt in range(retries):
        try:
            connection = mysql.connector.connect(**MYSQL_CONFIG)
            if connection.is_connected():
                return connection
        except Error as e:
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                raise
    return None

def get_mongo_connection(retries: int = 5, delay: int = 5) -> Optional[MongoClient]:
    """Establish connection to MongoDB with retry logic."""
    for attempt in range(retries):
        try:
            client = MongoClient(MONGO_URI)
            # Test the connection
            client.admin.command('ping')
            return client
        except errors.ServerSelectionTimeoutError as e:
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                raise
    return None

def get_mysql_data() -> List[tuple]:
    """Fetch min_value and max_value from MySQL database."""
    connection = None
    try:
        connection = get_mysql_connection()
        if not connection:
            return []

        cursor = connection.cursor()
        cursor.execute("SELECT min_value, max_value FROM data_points")  
        result = cursor.fetchall()  # Fetch all rows

        return result  # Returns a list of tuples [(min1, max1), (min2, max2), ...]

    except Error as err:
        print(f"Error fetching data from MySQL: {err}")
        return []

    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

def compute_statistics(values: List[tuple]) -> Dict[str, Optional[float]]:
    """Compute min, max, average, and median based on min & max."""
    if not values:
        return {
            "min": None,
            "max": None,
            "average": None,
            "median": None,
            "count": 0,
            "timestamp": time.time()
        }

    try:
        # Flatten the list of tuples into a single list of values
        min_values = [val[0] for val in values]  # Extract all min values
        max_values = [val[1] for val in values]  # Extract all max values

        # Combine the min and max values into one list for computing statistics
        combined_values = min_values + max_values

        # Compute the statistics
        min_val = min(combined_values)
        max_val = max(combined_values)
        avg = (min_val + max_val) / 2  # Compute average using only min and max
        median = float(sorted(combined_values)[len(combined_values) // 2])  # Approx median

        stats = {
            "min": float(min_val),
            "max": float(max_val),
            "average": float(avg),
            "median": median,
            "count": len(combined_values),
            "timestamp": time.time()
        }
        return stats

    except Exception as e:
        print(f"Error calculating statistics: {e}")
        return {
            "min": None,
            "max": None,
            "average": None,
            "median": None,
            "count": 0,
            "timestamp": time.time()
        }

def insert_to_mongodb(stats: Dict[str, Optional[float]]) -> bool:
    """Insert statistics into MongoDB."""
    client = None
    try:
        client = get_mongo_connection()
        if not client:
            return False

        db = client[MONGO_DB]
        collection = db[MONGO_COLLECTION]

        # Update or insert the statistics
        result = collection.replace_one(
            {"type": "descriptive_statistics"},
            {"type": "descriptive_statistics", **stats},
            upsert=True
        )
        return True

    except Exception as e:
        print(f"Error inserting data to MongoDB: {e}")
        return False

    finally:
        if client:
            client.close()

def main():
    """Main execution loop."""
    while True:
        try:
            # Fetch data from MySQL
            values = get_mysql_data()
            
            if values:
                # Compute statistics
                stats = compute_statistics(values)
                
                # Insert stats into MongoDB
                insert_to_mongodb(stats)

        except Exception as e:
            print(f"Error in main processing loop: {e}")

        # Wait before next iteration
        time.sleep(5)

if __name__ == "__main__":
    main()
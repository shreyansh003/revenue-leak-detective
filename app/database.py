import os
import psycopg2
from dotenv import load_dotenv


# Load environment variables from .env
load_dotenv()


def get_connection():
    connection = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("DB_NAME", "revenue_leak_db"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD")
    )

    return connection
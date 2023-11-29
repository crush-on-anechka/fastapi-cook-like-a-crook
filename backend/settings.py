import os

from dotenv import load_dotenv

load_dotenv()

DB = os.environ.get('POSTGRES_DB')
USER = os.environ.get('POSTGRES_USER')
PASS = os.environ.get('POSTGRES_PASSWORD')
PASS = os.environ.get('POSTGRES_PASSWORD')
HOST = os.environ.get('POSTGRES_HOST', 'db')
PORT = os.environ.get('POSTGRES_PORT', 5555)

POSTGRES_URL = (
    # f'postgresql+asyncpg://{USER}:{PASS}@{HOST}:5432/{DB}'  # when app and db running in Docker
    f'postgresql+asyncpg://{USER}:{PASS}@localhost:{PORT}/{DB}'  # when app running locally
    # 'postgresql+asyncpg://postgres:postgres@localhost:5432/alco_test_db'  # when using local db
)

PAGE_LIMIT = 10

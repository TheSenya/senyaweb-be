from sqlmodel import SQLModel, create_engine, Session
import os

# Use SQLite for simplicity. 
# check_same_thread=False is needed for SQLite with FastAPI/multithreading

# Use /app/data directory in Docker (has write permissions for appuser)
# Falls back to current directory for local development
data_dir = os.environ.get("DATA_DIR", ".")
os.makedirs(data_dir, exist_ok=True)

sqlite_file_name = os.path.join(data_dir, "database.db")
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})

def create_db_and_tables():
    """
    Creates tables from SQLModel metadata.
    Call this on app startup.
    """
    SQLModel.metadata.create_all(engine)

def get_session():
    """
    Dependency to get a database session.
    """
    with Session(engine) as session:
        yield session

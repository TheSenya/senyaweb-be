from sqlmodel import SQLModel, create_engine, Session

# Use SQLite for simplicity. 
# check_same_thread=False is needed for SQLite with FastAPI/multithreading
sqlite_file_name = "database.db"
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

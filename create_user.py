from sqlmodel import Session, select
from app.core.db import engine, create_db_and_tables
from app.models.user import User
from app.core.security import get_password_hash

def create_user(email: str, password: str):
    # Ensure DB exists
    create_db_and_tables()
    
    with Session(engine) as session:
        # Check if user exists
        statement = select(User).where(User.email == email)
        user = session.exec(statement).first()
        
        if user:
            print(f"User {email} already exists.")
            return
            
        hashed_password = get_password_hash(password)
        user = User(email=email, hashed_password=hashed_password)
        session.add(user)
        session.commit()
        print(f"User {email} created successfully!")

if __name__ == "__main__":
    email = input("Enter email: ")
    password = input("Enter password: ")
    create_user(email, password)

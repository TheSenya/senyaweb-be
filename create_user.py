"""
User creation utility script.

Usage:
    python create_user.py                    # Create regular user
    python create_user.py --admin            # Create admin user
    python create_user.py --make-admin       # Upgrade existing user to admin
"""

from sqlmodel import Session, select
from app.core.db import engine, create_db_and_tables
from app.models.user import User
from app.core.security import get_password_hash
import argparse


def create_user(email: str, password: str, is_admin: bool = False):
    """Create a new user in the database."""
    create_db_and_tables()
    
    with Session(engine) as session:
        # Check if user exists
        statement = select(User).where(User.email == email)
        user = session.exec(statement).first()
        
        if user:
            print(f"❌ User {email} already exists.")
            return False
            
        hashed_password = get_password_hash(password)
        user = User(
            email=email, 
            hashed_password=hashed_password,
            is_superuser=is_admin
        )
        session.add(user)
        session.commit()
        
        role = "admin" if is_admin else "regular user"
        print(f"✅ User {email} created successfully as {role}!")
        return True


def make_admin(email: str):
    """Upgrade an existing user to admin status."""
    create_db_and_tables()
    
    with Session(engine) as session:
        statement = select(User).where(User.email == email)
        user = session.exec(statement).first()
        
        if not user:
            print(f"❌ User {email} not found.")
            return False
        
        if user.is_superuser:
            print(f"ℹ️  User {email} is already an admin.")
            return True
            
        user.is_superuser = True
        session.add(user)
        session.commit()
        
        print(f"✅ User {email} has been upgraded to admin!")
        return True


def list_users():
    """List all users in the database."""
    create_db_and_tables()
    
    with Session(engine) as session:
        statement = select(User)
        users = session.exec(statement).all()
        
        if not users:
            print("No users found.")
            return
        
        print("\n" + "=" * 60)
        print("USERS")
        print("=" * 60)
        for user in users:
            role = "👑 ADMIN" if user.is_superuser else "👤 User"
            status = "✅ Active" if user.is_active else "❌ Inactive"
            print(f"{role} | {status} | {user.email}")
        print("=" * 60 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="User management utility")
    parser.add_argument("--admin", action="store_true", help="Create user as admin")
    parser.add_argument("--make-admin", metavar="EMAIL", help="Upgrade existing user to admin")
    parser.add_argument("--list", action="store_true", help="List all users")
    
    args = parser.parse_args()
    
    if args.list:
        list_users()
    elif args.make_admin:
        make_admin(args.make_admin)
    else:
        email = input("Enter email: ")
        password = input("Enter password: ")
        create_user(email, password, is_admin=args.admin)

# create_new_user.py
from models import create_user, get_user_by_username

def main():
    # CUSTOMIZE THESE VALUES:
    username = "newuser"  # Change this to your desired username
    password = "newpass123"  # Change this to your desired password
    role = "user"  # Can be "user" or "admin"
    
    # Optional: Add a database schema for the user
    schema = None  # Set to your database schema if needed
    
    existing = get_user_by_username(username)
    if existing:
        print(f"❌ User '{username}' already exists!")
        return
    
    user = create_user(username, password, role=role, schema=schema)
    print(f"✅ Created user: {user.username}")
    print(f"   Role: {user.role}")
    print(f"   ID: {user.id}")

if __name__ == "__main__":
    main()

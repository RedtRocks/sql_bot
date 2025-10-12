# admin_create.py
from models import create_user, get_user_by_username

def main():
    username = "admin"
    password = "tushar7"   # change to the password you want
    existing = get_user_by_username(username)
    if existing:
        print("Admin already exists:", existing.username)
        return
    user = create_user(username, password, role="admin")
    print("Created admin:", user.username, "role:", user.role)

if __name__ == "__main__":
    main()

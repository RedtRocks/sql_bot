# view_users.py
import os
from dotenv import load_dotenv
from database.postgres_connection import get_connection

# Load environment variables from .env file
load_dotenv()

def main():
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT id, username, role, created_at, 
                   CASE WHEN schema IS NOT NULL THEN 'Yes' ELSE 'No' END as has_schema,
                   CASE WHEN admin_schema IS NOT NULL THEN 'Yes' ELSE 'No' END as has_admin_schema
            FROM users 
            ORDER BY created_at DESC
        """)
        
        users = cursor.fetchall()
        
        if not users:
            print("❌ No users found in the database")
            return
        
        print("\n" + "="*80)
        print("📋 EXISTING USERS IN DATABASE")
        print("="*80)
        
        for user in users:
            user_id, username, role, created_at, has_schema, has_admin_schema = user
            print(f"\n👤 User ID: {user_id}")
            print(f"   Username: {username}")
            print(f"   Role: {role}")
            print(f"   Has Schema: {has_schema}")
            print(f"   Has Admin Schema: {has_admin_schema}")
            print(f"   Created: {created_at}")
            print("-" * 80)
        
        print(f"\n✅ Total users: {len(users)}")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"❌ Error fetching users: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()

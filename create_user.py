#!/usr/bin/env python3
"""
User Management Script for AI Assistant
Create and manage users in the system
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.security.auth import USERS_DB, get_password_hash, pwd_context
from app.security.auth import UserCreate, create_user


def create_user_sync(email: str, password: str, name: str, admin: bool = False) -> dict:
    """
    Create a new user synchronously
    """
    try:
        # Check if user already exists
        if email in USERS_DB:
            return {"error": f"User {email} already exists"}
        
        # Generate user ID
        user_id = f"user_{len(USERS_DB) + 1}"
        
        # Set scopes based on admin flag
        scopes = ["admin", "basic", "search", "generate"] if admin else ["basic", "search"]
        
        # Set budget limit based on admin flag
        budget_limit = 10000.0 if admin else 1000.0
        
        # Create user record
        user_record = {
            "user_id": user_id,
            "email": email,
            "name": name,
            "hashed_password": pwd_context.hash(password),
            "is_active": True,
            "scopes": scopes,
            "budget_limit": budget_limit,
            "current_usage": 0.0,
        }
        
        # Add to database
        USERS_DB[email] = user_record
        
        return {
            "success": True,
            "user_id": user_id,
            "email": email,
            "name": name,
            "scopes": scopes,
            "budget_limit": budget_limit
        }
        
    except Exception as e:
        return {"error": f"Failed to create user: {str(e)}"}


def list_users() -> dict:
    """
    List all users in the system
    """
    users = []
    for email, user_data in USERS_DB.items():
        users.append({
            "user_id": user_data["user_id"],
            "email": email,
            "name": user_data["name"],
            "is_active": user_data["is_active"],
            "scopes": user_data["scopes"],
            "budget_limit": user_data["budget_limit"],
            "current_usage": user_data["current_usage"]
        })
    
    return {
        "users": users,
        "total_users": len(users)
    }


def delete_user(email: str) -> dict:
    """
    Delete a user from the system
    """
    if email not in USERS_DB:
        return {"error": f"User {email} not found"}
    
    try:
        user_data = USERS_DB.pop(email)
        return {
            "success": True,
            "deleted_user": {
                "user_id": user_data["user_id"],
                "email": email,
                "name": user_data["name"]
            }
        }
    except Exception as e:
        return {"error": f"Failed to delete user: {str(e)}"}


def update_user_password(email: str, new_password: str) -> dict:
    """
    Update user password
    """
    if email not in USERS_DB:
        return {"error": f"User {email} not found"}
    
    try:
        USERS_DB[email]["hashed_password"] = pwd_context.hash(new_password)
        return {
            "success": True,
            "message": f"Password updated for user {email}"
        }
    except Exception as e:
        return {"error": f"Failed to update password: {str(e)}"}


def show_user_info(email: str) -> dict:
    """
    Show detailed user information
    """
    if email not in USERS_DB:
        return {"error": f"User {email} not found"}
    
    user_data = USERS_DB[email]
    return {
        "user_id": user_data["user_id"],
        "email": email,
        "name": user_data["name"],
        "is_active": user_data["is_active"],
        "scopes": user_data["scopes"],
        "budget_limit": user_data["budget_limit"],
        "current_usage": user_data["current_usage"],
        "is_admin": "admin" in user_data["scopes"]
    }


def main():
    """
    Main CLI interface
    """
    parser = argparse.ArgumentParser(
        description="AI Assistant User Management Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create a regular user
  python create_user.py create --email user@example.com --password secret123 --name "John Doe"
  
  # Create an admin user
  python create_user.py create --email admin@example.com --password admin123 --name "Admin User" --admin
  
  # List all users
  python create_user.py list
  
  # Show user info
  python create_user.py info --email user@example.com
  
  # Update password
  python create_user.py password --email user@example.com --new-password newpass123
  
  # Delete user
  python create_user.py delete --email user@example.com
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Create user command
    create_parser = subparsers.add_parser("create", help="Create a new user")
    create_parser.add_argument("--email", required=True, help="User email")
    create_parser.add_argument("--password", required=True, help="User password")
    create_parser.add_argument("--name", required=True, help="User full name")
    create_parser.add_argument("--admin", action="store_true", help="Create admin user")
    
    # List users command
    list_parser = subparsers.add_parser("list", help="List all users")
    
    # Show user info command
    info_parser = subparsers.add_parser("info", help="Show user information")
    info_parser.add_argument("--email", required=True, help="User email")
    
    # Update password command
    password_parser = subparsers.add_parser("password", help="Update user password")
    password_parser.add_argument("--email", required=True, help="User email")
    password_parser.add_argument("--new-password", required=True, help="New password")
    
    # Delete user command
    delete_parser = subparsers.add_parser("delete", help="Delete a user")
    delete_parser.add_argument("--email", required=True, help="User email")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Execute command
    if args.command == "create":
        result = create_user_sync(args.email, args.password, args.name, args.admin)
        if "error" in result:
            print(f"❌ Error: {result['error']}")
            sys.exit(1)
        else:
            print(f"✅ User created successfully:")
            print(f"  User ID: {result['user_id']}")
            print(f"  Email: {result['email']}")
            print(f"  Name: {result['name']}")
            print(f"  Scopes: {', '.join(result['scopes'])}")
            print(f"  Budget: ${result['budget_limit']}")
    
    elif args.command == "list":
        result = list_users()
        print(f"📋 Users in system ({result['total_users']} total):")
        for user in result['users']:
            admin_badge = "👑 " if "admin" in user['scopes'] else ""
            active_badge = "✅" if user['is_active'] else "❌"
            print(f"  {admin_badge}{user['email']} ({user['name']}) {active_badge}")
            print(f"    ID: {user['user_id']}")
            print(f"    Scopes: {', '.join(user['scopes'])}")
            print(f"    Budget: ${user['budget_limit']} (used: ${user['current_usage']})")
            print()
    
    elif args.command == "info":
        result = show_user_info(args.email)
        if "error" in result:
            print(f"❌ Error: {result['error']}")
            sys.exit(1)
        else:
            admin_badge = "👑 Admin" if result['is_admin'] else "👤 User"
            active_badge = "✅ Active" if result['is_active'] else "❌ Inactive"
            print(f"👤 User Information:")
            print(f"  Email: {result['email']}")
            print(f"  Name: {result['name']}")
            print(f"  User ID: {result['user_id']}")
            print(f"  Type: {admin_badge}")
            print(f"  Status: {active_badge}")
            print(f"  Scopes: {', '.join(result['scopes'])}")
            print(f"  Budget: ${result['budget_limit']}")
            print(f"  Current Usage: ${result['current_usage']}")
    
    elif args.command == "password":
        result = update_user_password(args.email, args.new_password)
        if "error" in result:
            print(f"❌ Error: {result['error']}")
            sys.exit(1)
        else:
            print(f"✅ {result['message']}")
    
    elif args.command == "delete":
        result = delete_user(args.email)
        if "error" in result:
            print(f"❌ Error: {result['error']}")
            sys.exit(1)
        else:
            print(f"✅ User deleted successfully:")
            print(f"  User ID: {result['deleted_user']['user_id']}")
            print(f"  Email: {result['deleted_user']['email']}")
            print(f"  Name: {result['deleted_user']['name']}")


if __name__ == "__main__":
    main() 
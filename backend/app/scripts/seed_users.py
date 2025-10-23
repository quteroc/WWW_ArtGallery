"""
Script to seed default users (admin and regular user).
Run with: python -m app.scripts.seed_users
"""
import asyncio
import sys
from app.db.session import async_session
from app.models.user import User
from app.core.security import get_password_hash
from sqlalchemy import select


async def seed_users():
    """
    Create or update default users:
    - admin (role=admin), password=admin123
    - user (role=user), password=user123
    
    Returns:
        0 on success, non-zero on error
    """
    try:
        async with async_session() as db:
            # Default users to create/update
            default_users = [
                {
                    "username": "admin",
                    "email": "admin@example.com",
                    "password": "admin123",
                    "role": "admin"
                },
                {
                    "username": "user",
                    "email": "user@example.com",
                    "password": "user123",
                    "role": "user"
                }
            ]
            
            for user_data in default_users:
                # Check if user exists
                query = select(User).where(User.username == user_data["username"])
                result = await db.execute(query)
                existing_user = result.scalar_one_or_none()
                
                if existing_user:
                    # Update existing user
                    existing_user.email = user_data["email"]
                    existing_user.hashed_password = get_password_hash(user_data["password"])
                    existing_user.role = user_data["role"]
                    existing_user.is_active = True
                    print(f"✅ Updated user: {user_data['username']} ({user_data['role']})")
                else:
                    # Create new user
                    new_user = User(
                        username=user_data["username"],
                        email=user_data["email"],
                        hashed_password=get_password_hash(user_data["password"]),
                        role=user_data["role"],
                        is_active=True
                    )
                    db.add(new_user)
                    print(f"✅ Created user: {user_data['username']} ({user_data['role']})")
            
            await db.commit()
            
            print("\n" + "="*60)
            print("DEFAULT USERS SEEDED SUCCESSFULLY!")
            print("="*60)
            print("You can now login with:")
            print("  Admin:   username=admin,   password=admin123")
            print("  User:    username=user,    password=user123")
            print("="*60)
            
            return 0
            
    except Exception as e:
        print(f"❌ Error seeding users: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


def main():
    """Run the seed users script."""
    exit_code = asyncio.run(seed_users())
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

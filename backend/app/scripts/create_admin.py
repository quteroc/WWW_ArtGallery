"""
Script to create or promote an admin user.
Run with: python -m app.scripts.create_admin --username <u> --email <e> --password <p>
"""
import asyncio
import argparse
import sys
from app.db.session import async_session
from app.models.user import User
from app.core.security import get_password_hash
from sqlalchemy import select, or_


async def create_or_promote_admin(username: str, email: str, password: str = None, db_session=None):
    """
    Create a new admin user or promote an existing user to admin.
    
    Args:
        username: Username for the admin account
        email: Email for the admin account
        password: Password for the admin account (required for new users, optional for existing)
        db_session: Optional database session (for testing)
    
    Returns:
        0 on success, non-zero on error
    """
    try:
        # Use provided session or create a new one
        if db_session:
            db = db_session
            should_commit = True
        else:
            db = async_session()
            await db.__aenter__()
            should_commit = True
        
        try:
            # Check if user with username or email exists
            query = select(User).where(
                or_(User.username == username, User.email == email)
            )
            result = await db.execute(query)
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                # User exists - promote to admin
                if existing_user.username != username or existing_user.email != email:
                    print(f"⚠️  User found with {'username' if existing_user.username == username else 'email'}")
                    print(f"   Username: {existing_user.username}")
                    print(f"   Email: {existing_user.email}")
                
                # Update role to admin
                existing_user.role = "admin"
                
                # Optionally update password if provided
                if password:
                    existing_user.hashed_password = get_password_hash(password)
                    print("✅ User promoted to admin and password updated!")
                else:
                    print("✅ User promoted to admin!")
                
                print(f"   Username: {existing_user.username}")
                print(f"   Email: {existing_user.email}")
                print(f"   Role: {existing_user.role}")
                
                await db.commit()
                return 0
            else:
                # User doesn't exist - create new admin
                if not password:
                    print("❌ Error: Password is required when creating a new user")
                    return 1
                
                new_admin = User(
                    email=email,
                    username=username,
                    hashed_password=get_password_hash(password),
                    role="admin"
                )
                db.add(new_admin)
                await db.commit()
                
                print("✅ Admin user created successfully!")
                print(f"   Username: {username}")
                print(f"   Email: {email}")
                print(f"   Role: admin")
                return 0
        finally:
            # Close session only if we created it
            if not db_session:
                await db.__aexit__(None, None, None)
                
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        if not db_session:
            try:
                await db.__aexit__(None, None, None)
            except:
                pass
        return 1


def main():
    """Parse command line arguments and create/promote admin."""
    parser = argparse.ArgumentParser(
        description="Create a new admin user or promote an existing user to admin role"
    )
    parser.add_argument(
        "--username",
        required=True,
        help="Username for the admin account"
    )
    parser.add_argument(
        "--email",
        required=True,
        help="Email for the admin account"
    )
    parser.add_argument(
        "--password",
        required=False,
        help="Password for the admin account (required for new users, optional for existing)"
    )
    
    args = parser.parse_args()
    
    # Basic validation
    if not args.username or not args.email:
        print("❌ Error: Username and email are required")
        sys.exit(1)
    
    # Run async function and exit with its return code
    exit_code = asyncio.run(create_or_promote_admin(args.username, args.email, args.password))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

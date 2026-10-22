import asyncio
import motor.motor_asyncio
from passlib.context import CryptContext

# Password hashing setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """Generates a bcrypt hash for the provided password string."""
    return pwd_context.hash(password)


# MongoDB connection setup
MONGO_DETAILS = "mongodb://localhost:27017"
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_DETAILS)
database = client.pdv_system
user_collection = database.get_collection("users")


async def create_admin_user():
    """Creates the initial admin user in the database if it does not exist."""
    admin_user = await user_collection.find_one({"username": "admin"})
    if not admin_user:
        print("Creating initial 'admin' user...")
        hashed_password = get_password_hash("admin123")  # Default admin password
        await user_collection.insert_one(
            {
                "username": "admin",
                "hashed_password": hashed_password,
                "role": "admin",
            }
        )
        print("Admin user created successfully!")
    else:
        print("Admin user already exists in database.")


if __name__ == "__main__":
    asyncio.run(create_admin_user())
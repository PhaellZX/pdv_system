import asyncio
import motor.motor_asyncio
from passlib.context import CryptContext

# Reutilizamos a função de hash do nosso app principal
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
def get_password_hash(password):
    return pwd_context.hash(password)

# Conexão com o MongoDB
MONGO_DETAILS = "mongodb://localhost:27017"
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_DETAILS)
database = client.pdv_system
user_collection = database.get_collection("usuarios")

async def create_admin_user():
    """Cria um usuário administrador inicial se ele não existir."""
    admin_user = await user_collection.find_one({"username": "admin"})
    if not admin_user:
        print("Criando usuário 'admin'...")
        hashed_password = get_password_hash("admin123") # Senha do admin
        await user_collection.insert_one({
            "username": "admin",
            "hashed_password": hashed_password,
            "role": "admin"
        })
        print("Usuário 'admin' criado com sucesso!")
    else:
        print("Usuário 'admin' já existe.")

if __name__ == "__main__":
    asyncio.run(create_admin_user())
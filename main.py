from datetime import date, datetime, timedelta, timezone
from typing import Annotated, Any, List, Optional

import motor.motor_asyncio
import pandas as pd
from bson import ObjectId
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from prophet import Prophet
from pydantic import BaseModel, Field, GetCoreSchemaHandler
from pydantic_core import core_schema

# --- Configuração para lidar com o ObjectId do MongoDB ---
class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        def validate(v: Any) -> ObjectId:
            if not ObjectId.is_valid(v):
                raise ValueError("ID de objeto inválido")
            return ObjectId(v)
        return core_schema.json_or_python_schema(
            python_schema=core_schema.with_info_plain_validator_function(
                lambda v, _: validate(v)
            ),
            json_schema=core_schema.str_schema(),
            serialization=core_schema.to_string_ser_schema(),
        )

# --- Configurações de Segurança ---
SECRET_KEY = "SUA_CHAVE_SECRETA_SUPER_COMPLEXA"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- Conexão com o Banco de Dados (MongoDB) ---
MONGO_DETAILS = "mongodb://localhost:27017"
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_DETAILS)
database = client.pdv_system
user_collection = database.get_collection("usuarios")
product_collection = database.get_collection("produtos")
sales_collection = database.get_collection("vendas")

# --- Modelos Pydantic (Schemas) ---
class TokenData(BaseModel): username: str | None = None
class User(BaseModel): username: str; role: str
class UserInDB(User): hashed_password: str
class UserCreate(BaseModel):
    username: str
    password: str
    role: str
class UserOut(BaseModel):
    username: str
    role: str
class ProductBase(BaseModel):
    name: str = Field(..., min_length=3)
    barcode: Optional[str] = None
    description: Optional[str] = None
    price_sell: float = Field(..., gt=0)
    stock_quantity: int = Field(..., ge=0)
    is_active: bool = True
class ProductCreate(ProductBase): pass
class ProductUpdate(BaseModel):
    name: Optional[str] = None; barcode: Optional[str] = None; description: Optional[str] = None
    price_sell: Optional[float] = None; stock_quantity: Optional[int] = None; is_active: Optional[bool] = None
class ProductInDB(ProductBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    class Config: json_encoders = {ObjectId: str}; allow_population_by_field_name = True
class SaleItem(BaseModel): product_id: str; quantity: int = Field(..., gt=0); unit_price: float
class SaleCreate(BaseModel): items: List[SaleItem]; total_amount: float; payment_method: str = "Dinheiro"; user_id: str
class SaleInDB(SaleCreate):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id"); sale_date: datetime = Field(default_factory=datetime.now)
    class Config: json_encoders = {ObjectId: str}; allow_population_by_field_name = True
class DashboardKPIs(BaseModel): total_revenue: float; total_sales: int; average_ticket: float
class TopProduct(BaseModel): product_name: str; total_sold: int
class ForecastPoint(BaseModel): date: date; predicted_sales: float

# --- Funções de Segurança e Dependências ---
def verify_password(p, h): return pwd_context.verify(p, h)
def get_password_hash(p): return pwd_context.hash(p)
async def get_user(u: str):
    if (d := await user_collection.find_one({"username": u})): return UserInDB(**d)
async def authenticate_user(u: str, p: str):
    user = await get_user(u)
    if not user or not verify_password(p, user.hashed_password): return None
    return user
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy(); expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15)); to_encode.update({"exp": expire}); return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    exc = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM]); username: str = payload.get("sub")
        if username is None: raise exc
    except JWTError: raise exc
    user = await get_user(username)
    if user is None: raise exc
    return user

# --- Inicialização do FastAPI ---
app = FastAPI(title="PDV System Backend")

# --- Endpoints de Autenticação e Usuário ---
@app.post("/token", summary="Gera um token de acesso para o usuário")
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user: raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário ou senha incorretos")
    access_token = create_access_token(data={"sub": user.username, "role": user.role}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=User, summary="Obtém os dados do usuário logado")
async def read_users_me(current_user: Annotated[User, Depends(get_current_user)]): return current_user

@app.post("/usuarios", response_model=UserOut, status_code=status.HTTP_201_CREATED, summary="Cria um novo usuário no sistema")
async def create_user(user_to_create: UserCreate, current_user: Annotated[User, Depends(get_current_user)]):
    if current_user.role != 'admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado: Somente administradores podem criar usuários.")
    if await user_collection.find_one({"username": user_to_create.username}):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"O nome de usuário '{user_to_create.username}' já está em uso.")
    
    hashed_password = get_password_hash(user_to_create.password)
    new_user_doc = {"username": user_to_create.username, "hashed_password": hashed_password, "role": user_to_create.role}
    await user_collection.insert_one(new_user_doc)
    return UserOut(**new_user_doc)

# --- Endpoints CRUD de Produtos ---
@app.post("/produtos", response_model=ProductInDB, status_code=status.HTTP_201_CREATED)
async def create_product(product: ProductCreate, current_user: Annotated[User, Depends(get_current_user)]):
    if product.barcode and await product_collection.find_one({"barcode": product.barcode}):
        raise HTTPException(status_code=409, detail=f"Produto com código de barras '{product.barcode}' já existe.")
    new_product = await product_collection.insert_one(product.dict()); return await product_collection.find_one({"_id": new_product.inserted_id})

@app.get("/produtos", response_model=List[ProductInDB])
async def list_products(current_user: Annotated[User, Depends(get_current_user)], search: Optional[str] = None, active_only: bool = True):
    query = {}
    if active_only: query["is_active"] = True
    if search: query["name"] = {"$regex": search, "$options": "i"}
    return await product_collection.find(query).to_list(1000)

@app.get("/produtos/lookup/{term}", response_model=ProductInDB)
async def lookup_product(term: str, current_user: Annotated[User, Depends(get_current_user)]):
    query = {"$or": [{"barcode": term}, {"name": {"$regex": f"^{term}$", "$options": "i"}}, {"_id": ObjectId(term) if ObjectId.is_valid(term) else None}], "is_active": True}
    if (p := await product_collection.find_one(query)): return p
    raise HTTPException(status_code=404, detail="Produto não encontrado")

@app.put("/produtos/{pid}", response_model=ProductInDB)
async def update_product(pid: str, p_up: ProductUpdate, current_user: Annotated[User, Depends(get_current_user)]):
    d = p_up.dict(exclude_unset=True)
    if len(d) >= 1: await product_collection.update_one({"_id": ObjectId(pid)}, {"$set": d})
    if (p := await product_collection.find_one({"_id": ObjectId(pid)})): return p
    raise HTTPException(status_code=404, detail=f"Produto {pid} não encontrado")

@app.delete("/produtos/{pid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(pid: str, current_user: Annotated[User, Depends(get_current_user)]):
    r = await product_collection.update_one({"_id": ObjectId(pid)}, {"$set": {"is_active": False}})
    if r.matched_count == 0: raise HTTPException(status_code=404, detail=f"Produto {pid} não encontrado")

# --- Endpoint de Venda ---
@app.post("/vendas", response_model=SaleInDB, status_code=status.HTTP_201_CREATED)
async def create_sale(sale: SaleCreate, current_user: Annotated[User, Depends(get_current_user)]):
    for item in sale.items:
        product = await product_collection.find_one({"_id": ObjectId(item.product_id)})
        if not product: raise HTTPException(status_code=404, detail=f"Produto ID {item.product_id} não encontrado.")
        if product["stock_quantity"] < item.quantity: raise HTTPException(status_code=400, detail=f"Estoque insuficiente para '{product['name']}'. Disponível: {product['stock_quantity']}")
    for item in sale.items: await product_collection.update_one({"_id": ObjectId(item.product_id)}, {"$inc": {"stock_quantity": -item.quantity}})
    sale_doc = sale.dict(); sale_doc["user_id"] = current_user.username; sale_doc["sale_date"] = datetime.now(timezone.utc)
    new_sale = await sales_collection.insert_one(sale_doc); return await sales_collection.find_one({"_id": new_sale.inserted_id})

# --- Endpoints de Dashboard e Relatórios ---
@app.get("/dashboard/kpis", response_model=DashboardKPIs)
async def get_dashboard_kpis(current_user: Annotated[User, Depends(get_current_user)]):
    pipeline = [{"$group": {"_id": None, "total_revenue": {"$sum": "$total_amount"}, "total_sales": {"$sum": 1}}}]
    result = await sales_collection.aggregate(pipeline).to_list(1)
    if not result: return DashboardKPIs(total_revenue=0, total_sales=0, average_ticket=0)
    kpis = result[0]
    average_ticket = kpis["total_revenue"] / kpis["total_sales"] if kpis["total_sales"] > 0 else 0
    return DashboardKPIs(total_revenue=kpis["total_revenue"], total_sales=kpis["total_sales"], average_ticket=average_ticket)
@app.get("/dashboard/top-products", response_model=List[TopProduct])
async def get_top_products(current_user: Annotated[User, Depends(get_current_user)], limit: int = 5):
    pipeline = [
        {"$unwind": "$items"}, {"$group": {"_id": "$items.product_id", "total_sold": {"$sum": "$items.quantity"}}},
        {"$sort": {"total_sold": -1}}, {"$limit": limit},
        {"$addFields": {"product_id_obj": {"$toObjectId": "$_id"}}},
        {"$lookup": {"from": "produtos", "localField": "product_id_obj", "foreignField": "_id", "as": "product_info"}},
        {"$unwind": "$product_info"}, {"$project": {"_id": 0, "product_name": "$product_info.name", "total_sold": "$total_sold"}}
    ]
    return await sales_collection.aggregate(pipeline).to_list(limit)

# --- Endpoint de Previsão de Vendas ---
@app.get("/previsao/produto/{product_id}", response_model=List[ForecastPoint])
async def get_sales_forecast(product_id: str, current_user: Annotated[User, Depends(get_current_user)], days_to_predict: int = 7):
    pipeline = [
        {"$unwind": "$items"}, {"$match": {"items.product_id": product_id}},
        {"$project": {"date": {"$toDate": "$sale_date"}, "quantity": "$items.quantity"}},
        {"$group": {"_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$date"}}, "total_quantity": {"$sum": "$quantity"}}},
        {"$sort": {"_id": 1}}
    ]
    sales_history = await sales_collection.aggregate(pipeline).to_list(length=None)
    if len(sales_history) < 2: raise HTTPException(status_code=400, detail="Não há dados históricos suficientes para gerar uma previsão.")
    
    df = pd.DataFrame(sales_history).rename(columns={"_id": "ds", "total_quantity": "y"})
    df['ds'] = pd.to_datetime(df['ds'])
    
    model = Prophet(daily_seasonality=True).fit(df)
    future = model.make_future_dataframe(periods=days_to_predict)
    forecast = model.predict(future)
    
    future_forecast = forecast[forecast['ds'] > df['ds'].max()]
    return [ForecastPoint(date=row['ds'].date(), predicted_sales=max(0, row['yhat'])) for _, row in future_forecast.iterrows()]
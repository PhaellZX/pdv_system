from datetime import date, datetime, timedelta, timezone
from typing import Annotated, Any, List, Optional

from bson import ObjectId
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
import motor.motor_asyncio
import pandas as pd
from passlib.context import CryptContext
from prophet import Prophet
from pydantic import BaseModel, Field, GetCoreSchemaHandler
from pydantic_core import core_schema


# --- MongoDB PyObjectId Type Handler ---
class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        def validate(v: Any) -> ObjectId:
            if not ObjectId.is_valid(v):
                raise ValueError("Invalid ObjectId string format")
            return ObjectId(v)

        return core_schema.json_or_python_schema(
            python_schema=core_schema.with_info_plain_validator_function(
                lambda v, _: validate(v)
            ),
            json_schema=core_schema.str_schema(),
            serialization=core_schema.to_string_ser_schema(),
        )


# --- Security Settings & Password Hashing ---
SECRET_KEY = "YOUR_SUPER_COMPLEX_SECRET_KEY_HERE"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- Database Connection (MongoDB) ---
MONGO_DETAILS = "mongodb://localhost:27017"
DATABASE_NAME = "pdv_system"
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_DETAILS)
db = client[DATABASE_NAME]

user_collection = db.get_collection("users")
product_collection = db.get_collection("products")
sales_collection = db.get_collection("sales")


# --- Pydantic Data Models (Schemas) ---
class TokenData(BaseModel):
    username: Optional[str] = None


class User(BaseModel):
    username: str
    role: str


class UserInDB(User):
    hashed_password: str


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


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    barcode: Optional[str] = None
    description: Optional[str] = None
    price_sell: Optional[float] = None
    stock_quantity: Optional[int] = None
    is_active: Optional[bool] = None


class ProductInDB(ProductBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")

    class Config:
        json_encoders = {ObjectId: str}
        allow_population_by_field_name = True


class SaleItem(BaseModel):
    product_id: str
    quantity: int = Field(..., gt=0)
    unit_price: float


class SaleCreate(BaseModel):
    items: List[SaleItem]
    total_amount: float
    payment_method: str = "Cash"
    user_id: str


class SaleInDB(SaleCreate):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    sale_date: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {ObjectId: str}
        allow_population_by_field_name = True


class DashboardKPIs(BaseModel):
    total_revenue: float
    total_sales: int
    average_ticket: float


class TopProduct(BaseModel):
    product_name: str
    total_sold: int


class ForecastPoint(BaseModel):
    date: date
    predicted_sales: float


class FullBackup(BaseModel):
    products: List[ProductInDB]
    users: List[UserInDB]
    sales: List[SaleInDB]


# --- Helper Security Functions ---
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


async def get_user(username: str) -> Optional[UserInDB]:
    if user_doc := await user_collection.find_one({"username": username}):
        return UserInDB(**user_doc)
    return None


async def authenticate_user(
    username: str, password: str
) -> Optional[UserInDB]:
    user = await get_user(username)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(
    data: dict, expires_delta: Optional[timedelta] = None
) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=15)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)]
) -> UserInDB:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate user credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await get_user(username)
    if user is None:
        raise credentials_exception
    return user


# --- FastAPI Application Initialization ---
app = FastAPI(title="POS System Backend API", version="1.0.0")


# --- Authentication & User Management Endpoints ---
@app.post("/token", summary="Generate JWT access token for authentication")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get(
    "/users/me",
    response_model=User,
    summary="Fetch current logged user profile",
)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_user)]
):
    return current_user


@app.post(
    "/users",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user in database",
)
async def create_user(
    user_to_create: UserCreate,
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Only administrator users can create accounts.",
        )
    if await user_collection.find_one({"username": user_to_create.username}):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"The username '{user_to_create.username}' is already taken.",
        )

    hashed_password = get_password_hash(user_to_create.password)
    new_user_doc = {
        "username": user_to_create.username,
        "hashed_password": hashed_password,
        "role": user_to_create.role,
    }
    await user_collection.insert_one(new_user_doc)
    return UserOut(**new_user_doc)


# --- Product Inventory CRUD Endpoints ---
@app.post(
    "/products",
    response_model=ProductInDB,
    status_code=status.HTTP_201_CREATED,
)
async def create_product(
    product: ProductCreate,
    current_user: Annotated[User, Depends(get_current_user)],
):
    if product.barcode and await product_collection.find_one(
        {"barcode": product.barcode}
    ):
        raise HTTPException(
            status_code=409,
            detail=f"Product with barcode '{product.barcode}' already exists.",
        )
    new_product = await product_collection.insert_one(product.dict())
    return await product_collection.find_one({"_id": new_product.inserted_id})


@app.get("/products", response_model=List[ProductInDB])
async def list_products(
    current_user: Annotated[User, Depends(get_current_user)],
    search: Optional[str] = None,
    active_only: bool = True,
):
    query = {}
    if active_only:
        query["is_active"] = True
    if search:
        query["name"] = {"$regex": search, "$options": "i"}
    return await product_collection.find(query).to_list(1000)


@app.get("/products/lookup/{term}", response_model=ProductInDB)
async def lookup_product(
    term: str, current_user: Annotated[User, Depends(get_current_user)]
):
    query = {
        "$or": [
            {"barcode": term},
            {"name": {"$regex": f"^{term}$", "$options": "i"}},
            {"_id": ObjectId(term) if ObjectId.is_valid(term) else None},
        ],
        "is_active": True,
    }
    if p := await product_collection.find_one(query):
        return p
    raise HTTPException(status_code=404, detail="Product not found")


@app.put("/products/{pid}", response_model=ProductInDB)
async def update_product(
    pid: str,
    p_up: ProductUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
):
    data = p_up.dict(exclude_unset=True)
    if len(data) >= 1:
        await product_collection.update_one(
            {"_id": ObjectId(pid)}, {"$set": data}
        )
    if p := await product_collection.find_one({"_id": ObjectId(pid)}):
        return p
    raise HTTPException(
        status_code=404, detail=f"Product '{pid}' was not found"
    )


@app.delete("/products/{pid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    pid: str, current_user: Annotated[User, Depends(get_current_user)]
):
    result = await product_collection.update_one(
        {"_id": ObjectId(pid)}, {"$set": {"is_active": False}}
    )
    if result.matched_count == 0:
        raise HTTPException(
            status_code=404, detail=f"Product '{pid}' was not found"
        )


# --- Checkout / Sales Endpoints ---
@app.post(
    "/sales",
    response_model=SaleInDB,
    status_code=status.HTTP_201_CREATED,
)
async def create_sale(
    sale: SaleCreate,
    current_user: Annotated[User, Depends(get_current_user)],
):
    # Verify inventory availability
    for item in sale.items:
        product = await product_collection.find_one(
            {"_id": ObjectId(item.product_id)}
        )
        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"Product ID '{item.product_id}' not found.",
            )
        if product["stock_quantity"] < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for '{product['name']}'. Available: {product['stock_quantity']}",
            )

    # Decrement stock count
    for item in sale.items:
        await product_collection.update_one(
            {"_id": ObjectId(item.product_id)},
            {"$inc": {"stock_quantity": -item.quantity}},
        )

    sale_doc = sale.dict()
    sale_doc["user_id"] = current_user.username
    sale_doc["sale_date"] = datetime.now(timezone.utc)
    new_sale = await sales_collection.insert_one(sale_doc)
    return await sales_collection.find_one({"_id": new_sale.inserted_id})


# --- Dashboard & KPI Metrics Endpoints ---
@app.get("/dashboard/kpis", response_model=DashboardKPIs)
async def get_dashboard_kpis(
    current_user: Annotated[User, Depends(get_current_user)]
):
    pipeline = [
        {
            "$group": {
                "_id": None,
                "total_revenue": {"$sum": "$total_amount"},
                "total_sales": {"$sum": 1},
            }
        }
    ]
    result = await sales_collection.aggregate(pipeline).to_list(1)
    if not result:
        return DashboardKPIs(
            total_revenue=0.0, total_sales=0, average_ticket=0.0
        )

    kpis = result[0]
    average_ticket = (
        kpis["total_revenue"] / kpis["total_sales"]
        if kpis["total_sales"] > 0
        else 0.0
    )
    return DashboardKPIs(
        total_revenue=kpis["total_revenue"],
        total_sales=kpis["total_sales"],
        average_ticket=average_ticket,
    )


@app.get("/dashboard/top-products", response_model=List[TopProduct])
async def get_top_products(
    current_user: Annotated[User, Depends(get_current_user)],
    limit: int = 5,
):
    pipeline = [
        {"$unwind": "$items"},
        {
            "$group": {
                "_id": "$items.product_id",
                "total_sold": {"$sum": "$items.quantity"},
            }
        },
        {"$sort": {"total_sold": -1}},
        {"$limit": limit},
        {"$addFields": {"product_id_obj": {"$toObjectId": "$_id"}}},
        {
            "$lookup": {
                "from": "products",
                "localField": "product_id_obj",
                "foreignField": "_id",
                "as": "product_info",
            }
        },
        {"$unwind": "$product_info"},
        {
            "$project": {
                "_id": 0,
                "product_name": "$product_info.name",
                "total_sold": "$total_sold",
            }
        },
    ]
    return await sales_collection.aggregate(pipeline).to_list(limit)


# --- Sales Forecasting Endpoints (Prophet Engine) ---
@app.get(
    "/forecast/product/{product_id}",
    response_model=List[ForecastPoint],
)
async def get_sales_forecast(
    product_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    days_to_predict: int = 7,
):
    pipeline = [
        {"$unwind": "$items"},
        {"$match": {"items.product_id": product_id}},
        {
            "$project": {
                "date": {"$toDate": "$sale_date"},
                "quantity": "$items.quantity",
            }
        },
        {
            "$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$date"}},
                "total_quantity": {"$sum": "$quantity"},
            }
        },
        {"$sort": {"_id": 1}},
    ]
    sales_history = await sales_collection.aggregate(pipeline).to_list(
        length=None
    )
    if len(sales_history) < 2:
        raise HTTPException(
            status_code=400,
            detail="Insufficient historical sales data to generate prediction model.",
        )

    df = pd.DataFrame(sales_history).rename(
        columns={"_id": "ds", "total_quantity": "y"}
    )
    df["ds"] = pd.to_datetime(df["ds"])

    model = Prophet(daily_seasonality=True).fit(df)
    future = model.make_future_dataframe(periods=days_to_predict)
    forecast = model.predict(future)

    future_forecast = forecast[forecast["ds"] > df["ds"].max()]
    return [
        ForecastPoint(
            date=row["ds"].date(), predicted_sales=max(0.0, row["yhat"])
        )
        for _, row in future_forecast.iterrows()
    ]


# --- Database Backup Import/Export Endpoints ---
def serialize_docs(docs: list) -> list:
    """Utility function to handle custom MongoDB BSON ObjectId serialization."""
    if not docs:
        return []
    return jsonable_encoder(docs, custom_encoder={ObjectId: str})


@app.get("/backup/export/full", response_model=FullBackup)
async def export_full_backup(
    current_user: Annotated[User, Depends(get_current_user)]
):
    products = await db["products"].find().to_list(length=None)
    users = await db["users"].find().to_list(length=None)
    sales = await db["sales"].find().to_list(length=None)

    return {
        "products": serialize_docs(products),
        "users": serialize_docs(users),
        "sales": serialize_docs(sales),
    }


@app.post("/backup/import/full")
async def import_full_backup(
    backup: FullBackup,
    current_user: Annotated[User, Depends(get_current_user)],
):
    await db["products"].delete_many({})
    await db["users"].delete_many({})
    await db["sales"].delete_many({})

    products_to_insert = [
        p.model_dump(by_alias=True, exclude={"id"}) for p in backup.products
    ]
    users_to_insert = [
        u.model_dump(by_alias=True, exclude={"id"}) for u in backup.users
    ]
    sales_to_insert = [
        s.model_dump(by_alias=True, exclude={"id"}) for s in backup.sales
    ]

    if products_to_insert:
        await db["products"].insert_many(products_to_insert)
    if users_to_insert:
        await db["users"].insert_many(users_to_insert)
    if sales_to_insert:
        await db["sales"].insert_many(sales_to_insert)

    return {"status": "success", "message": "Backup imported successfully."}
from datetime import datetime, timedelta

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

from config import MONGO_URI, DB_NAME

client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]

users_col = db["users"]
channels_col = db["channels"]
movies_col = db["movies"]
prices_col = db["prices"]
payments_col = db["payments"]
comments_col = db["comments"]
saved_col = db["saved_movies"]


# ---------------- USERS ----------------
async def add_user(user_id: int, username: str | None):
    await users_col.update_one(
        {"_id": user_id},
        {
            "$setOnInsert": {
                "_id": user_id,
                "username": username,
                "joined_at": datetime.utcnow(),
                "vip_until": None,
            }
        },
        upsert=True,
    )
    if username:
        await users_col.update_one({"_id": user_id}, {"$set": {"username": username}})


async def get_user(user_id: int):
    return await users_col.find_one({"_id": user_id})


async def all_user_ids():
    cursor = users_col.find({}, {"_id": 1})
    return [doc["_id"] async for doc in cursor]


async def users_count() -> int:
    return await users_col.count_documents({})


async def set_vip(user_id: int, days: int):
    user = await get_user(user_id)
    base = datetime.utcnow()
    if user and user.get("vip_until") and user["vip_until"] > base:
        base = user["vip_until"]
    until = base + timedelta(days=days)
    await users_col.update_one({"_id": user_id}, {"$set": {"vip_until": until}}, upsert=True)
    return until


async def is_vip(user_id: int) -> bool:
    user = await get_user(user_id)
    if not user or not user.get("vip_until"):
        return False
    return user["vip_until"] > datetime.utcnow()


# ---------------- CHANNELS ----------------
async def add_channel(chat_id: int, title: str, username: str | None, link: str):
    await channels_col.update_one(
        {"_id": chat_id},
        {"$set": {"title": title, "username": username, "link": link}},
        upsert=True,
    )


async def remove_channel(chat_id: int):
    await channels_col.delete_one({"_id": chat_id})


async def get_channels():
    return await channels_col.find().to_list(length=100)


# ---------------- MOVIES ----------------
async def add_movie(code: str, file_id: str, content_type: str, title: str = "", is_premium: bool = False):
    await movies_col.update_one(
        {"_id": str(code)},
        {
            "$set": {
                "file_id": file_id,
                "content_type": content_type,  # "video" | "document"
                "title": title,
                "is_premium": is_premium,
                "added_at": datetime.utcnow(),
            },
            "$setOnInsert": {"views": 0},
        },
        upsert=True,
    )


async def get_movie(code: str):
    return await movies_col.find_one({"_id": str(code)})


async def delete_movie(code: str):
    await movies_col.delete_one({"_id": str(code)})


async def inc_views(code: str):
    await movies_col.update_one({"_id": str(code)}, {"$inc": {"views": 1}})


async def get_random_movie():
    result = await movies_col.aggregate([{"$sample": {"size": 1}}]).to_list(length=1)
    return result[0] if result else None


async def get_top_movies(limit: int = 10):
    return await movies_col.find().sort("views", -1).limit(limit).to_list(length=limit)


async def get_last_movies(limit: int = 10):
    return await movies_col.find().sort("added_at", -1).limit(limit).to_list(length=limit)


async def movies_count() -> int:
    return await movies_col.count_documents({})


# ---------------- PRICES (VIP tariflar) ----------------
DEFAULT_PRICES = {"_id": "plans", "1m": 10000, "3m": 25000, "1y": 75000}


async def get_prices():
    p = await prices_col.find_one({"_id": "plans"})
    if not p:
        await prices_col.insert_one(DEFAULT_PRICES)
        p = DEFAULT_PRICES
    return p


async def set_price(plan: str, amount: int):
    await prices_col.update_one({"_id": "plans"}, {"$set": {plan: amount}}, upsert=True)


PLAN_DAYS = {"1m": 30, "3m": 90, "1y": 365}
PLAN_NAMES = {"1m": "1 oylik", "3m": "3 oylik", "1y": "1 yillik"}


# ---------------- PAYMENTS ----------------
async def create_payment(user_id: int, plan: str, amount: int, method: str):
    payment = {
        "user_id": user_id,
        "plan": plan,
        "amount": amount,
        "method": method,
        "status": "pending",
        "created_at": datetime.utcnow(),
    }
    res = await payments_col.insert_one(payment)
    return res.inserted_id


async def get_pending_payment(user_id: int):
    return await payments_col.find_one(
        {"user_id": user_id, "status": "pending"}, sort=[("created_at", -1)]
    )


async def get_payment(payment_id):
    if isinstance(payment_id, str):
        payment_id = ObjectId(payment_id)
    return await payments_col.find_one({"_id": payment_id})


async def confirm_payment(payment_id):
    if isinstance(payment_id, str):
        payment_id = ObjectId(payment_id)
    await payments_col.update_one(
        {"_id": payment_id}, {"$set": {"status": "confirmed", "confirmed_at": datetime.utcnow()}}
    )


async def reject_payment(payment_id):
    if isinstance(payment_id, str):
        payment_id = ObjectId(payment_id)
    await payments_col.update_one({"_id": payment_id}, {"$set": {"status": "rejected"}})


# ---------------- COMMENTS ----------------
async def add_comment(code: str, user_id: int, username: str | None, text: str):
    await comments_col.insert_one(
        {
            "code": str(code),
            "user_id": user_id,
            "username": username,
            "text": text,
            "created_at": datetime.utcnow(),
        }
    )


async def get_comments(code: str, limit: int = 5):
    return (
        await comments_col.find({"code": str(code)})
        .sort("created_at", -1)
        .limit(limit)
        .to_list(length=limit)
    )


async def comments_count(code: str) -> int:
    return await comments_col.count_documents({"code": str(code)})


# ---------------- SAVED MOVIES ----------------
async def save_movie(user_id: int, code: str):
    await saved_col.update_one(
        {"user_id": user_id, "code": str(code)},
        {"$setOnInsert": {"user_id": user_id, "code": str(code), "saved_at": datetime.utcnow()}},
        upsert=True,
    )


async def get_saved_movies(user_id: int, limit: int = 20):
    return (
        await saved_col.find({"user_id": user_id})
        .sort("saved_at", -1)
        .limit(limit)
        .to_list(length=limit)
    )

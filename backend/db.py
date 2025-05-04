import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

# connect
client = MongoClient(os.getenv("MONGO_URI"))
db     = client["cloud_game_db"]

# ensure collections exist (optional—Mongo will auto-create on first insert)
for name in ("users", "admins", "games", "ratings"):
    if name not in db.list_collection_names():
        db.create_collection(name)

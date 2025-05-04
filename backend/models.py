# backend/models.py
from db import db

users_collection    = db.users
admins_collection   = db.admins
games_collection    = db.games
ratings_collection  = db.ratings
comments_collection = db.comments    # ← add this line

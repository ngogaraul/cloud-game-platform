from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from models import games_collection, users_collection
from utils.jwt_handler import admin_required
from flask import abort
from bson import ObjectId
admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/games", methods=["POST"])
@jwt_required()
@admin_required
def create_game():
    data = request.get_json()
    name            = data.get("name","").strip()
    genres          = data.get("genres", [])
    photo           = data.get("photo","")
    optional        = data.get("optional", {})
    rating_enabled  = bool(data.get("rating_enabled", True))
    comment_enabled = bool(data.get("comment_enabled", True))

    if not name or not isinstance(genres, list):
        return jsonify(msg="`name` (string) and `genres` (array) required"), 400

    result = games_collection.insert_one({
        "name":            name,
        "genres":          genres,
        "photo":           photo,
        "optional":        optional,
        "ratings":         {"average": None, "count": 0},
        "comments":        {"count": 0, "list": []},
        "rating_enabled":  rating_enabled,
        "comment_enabled": comment_enabled,
        "created_by":      get_jwt_identity()
    })
    return jsonify(msg="Game created", game_id=str(result.inserted_id)), 201

@admin_bp.route("/games/<game_id>", methods=["DELETE"])
@jwt_required()
@admin_required
def delete_game(game_id):
    res = games_collection.delete_one({"_id": ObjectId(game_id)})
    if res.deleted_count == 0:
        return jsonify(msg="Game not found"), 404
    return jsonify(msg="Game deleted"), 200

@admin_bp.route("/users", methods=["GET"])
@jwt_required()
@admin_required
def list_users():
    out = []
    for u in users_collection.find({}, {"password": 0}):
        u["_id"] = str(u["_id"])
        out.append(u)
    return jsonify(out), 200


@admin_bp.route("/games/<game_id>/settings", methods=["PATCH"])
@jwt_required()
@admin_required
def update_game_settings(game_id):
    """
    Toggle rating_enabled and/or comment_enabled on a game.
    Body can include one or both of:
      { "rating_enabled": true/false,
        "comment_enabled": true/false }
    """
    data = request.get_json() or {}
    updates = {}
    if "rating_enabled" in data:
        updates["rating_enabled"] = bool(data["rating_enabled"])
    if "comment_enabled" in data:
        updates["comment_enabled"] = bool(data["comment_enabled"])

    if not updates:
        return jsonify(msg="No valid settings provided"), 400

    res = games_collection.update_one(
        {"_id": ObjectId(game_id)},
        {"$set": updates}
    )
    if res.matched_count == 0:
        return jsonify(msg="Game not found"), 404

    return jsonify(
        msg="Settings updated",
        game_id=game_id,
        updated=updates
    ), 200
# backend/routes/admin.py (add below existing routes)

@admin_bp.route("/users/<user_id>", methods=["DELETE"])
@jwt_required()
@admin_required
def delete_user(user_id):
    """
    Delete a user by their MongoDB _id.
    """
    res = users_collection.delete_one({"_id": ObjectId(user_id)})
    if res.deleted_count == 0:
        return jsonify(msg="User not found"), 404
    return jsonify(msg="User deleted"), 200
from werkzeug.security import generate_password_hash

@admin_bp.route("/users", methods=["POST"])
@jwt_required()
@admin_required
def create_user():
    data     = request.get_json() or {}
    username = data.get("username", "").strip()
    email    = data.get("email", "").strip()
    password = data.get("password", "")
    is_admin = bool(data.get("is_admin", False))

    if not username or not email or not password:
        return jsonify(msg="Missing fields"), 400
    if users_collection.find_one({"email": email}):
        return jsonify(msg="Email already registered"), 409

    pw_hash = generate_password_hash(password)
    result  = users_collection.insert_one({
        "username": username,
        "email":    email,
        "password": pw_hash,
        "is_admin": is_admin
    })
    if is_admin:
        admins_collection.insert_one({"user_id": result.inserted_id})

    return jsonify(msg="User added successfully", user_id=str(result.inserted_id)), 201
@admin_bp.route("/games", methods=["GET"])
@jwt_required()
@admin_required
def get_all_games():
    """
    Return all games with only name, genres, and rating.
    """
    games = []
    for g in games_collection.find({}, {"name": 1, "genres": 1, "ratings.average": 1}):
        games.append({
            "id": str(g["_id"]),
            "name": g.get("name"),
            "genres": g.get("genres", []),
            "rating": g.get("ratings", {}).get("average")
        })
    return jsonify(games), 200


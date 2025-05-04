from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from models import users_collection, games_collection, ratings_collection, comments_collection
from utils.rating_utils import calculate_average_rating

user_bp = Blueprint("user", __name__)

@user_bp.route("/profile", methods=["GET"])
@jwt_required()
def profile():
    uid  = get_jwt_identity()
    #user = users_collection.find_one({"_id": ObjectId(uid)}, {"password": 0, "played": 1})
    user = users_collection.find_one(
        {"_id": ObjectId(uid)},
        {"password": 0}
    )

    if not user:
        return jsonify(msg="User not found"), 404
    user["_id"] = str(user["_id"])
    # Return played time per game in hours
    user["played"] = { gid: hours for gid, hours in user.get("played", {}).items() }
    return jsonify(user), 200

@user_bp.route("/games", methods=["GET"])
@jwt_required()
def list_games():
    out = []
    for g in games_collection.find():
        gid = str(g["_id"])
        # get real-time ratings
        rating_info = calculate_average_rating(gid)
        # get comments
        comment_cursor = comments_collection.find({"game_id": gid})
        comments = [{ "user_id": c["user_id"], "comment": c["comment"] } for c in comment_cursor]
        out.append({
            "_id":             gid,
            "name":            g["name"],
            "genres":          g.get("genres", []),
            "photo":           g.get("photo", ""),
            "optional":        g.get("optional", {}),
            "ratings":         rating_info,
            "comments":        { "count": len(comments), "list": comments },
            "rating_enabled":  g.get("rating_enabled", True),
            "comment_enabled": g.get("comment_enabled", True),
        })
    return jsonify(out), 200

@user_bp.route("/games/<game_id>/play", methods=["POST"])
@jwt_required()
def play_game(game_id):
    uid = get_jwt_identity()
    # Verify the game exists
    g = games_collection.find_one({"_id": ObjectId(game_id)})
    if not g:
        return jsonify(msg="Game not found"), 404

    # Increment play time (in hours) for the user for this game
    users_collection.update_one(
        {"_id": ObjectId(uid)},
        {"$inc": {f"played.{game_id}": 1}}
    )
    # Retrieve updated play time
    user = users_collection.find_one({"_id": ObjectId(uid)}, {"played": 1})
    play_time = user.get("played", {}).get(game_id, 0)
    return jsonify(msg="Play recorded", play_time_hours=play_time), 200

@user_bp.route("/games/<game_id>/rate", methods=["POST"])
@jwt_required()
def rate_game(game_id):
    uid  = get_jwt_identity()
    g    = games_collection.find_one({"_id": ObjectId(game_id)})
    if not g or not g.get("rating_enabled", True):
        return jsonify(msg="Rating not allowed"), 403

    data   = request.get_json() or {}
    rating = data.get("rating")
    if rating is None or not (1 <= rating <= 5):
        return jsonify(msg="Invalid rating"), 400

    ratings_collection.insert_one({
        "game_id": game_id,
        "user_id": uid,
        "rating":  rating
    })
    return jsonify(
        msg        = "Rating submitted",
        avg_rating = calculate_average_rating(game_id)
    ), 201

@user_bp.route("/games/<game_id>/comment", methods=["POST"])
@jwt_required()
def comment_game(game_id):
    uid = get_jwt_identity()
    g = games_collection.find_one({"_id": ObjectId(game_id)})
    if not g or not g.get("comment_enabled", True):
        return jsonify(msg="Commenting not allowed"), 403

    data = request.get_json() or {}
    text = data.get("comment", "").strip()
    if not text:
        return jsonify(msg="Empty comment"), 400

    comments_collection.insert_one({
        "game_id": game_id,
        "user_id": uid,
        "comment": text
    })
    return jsonify(msg="Comment added"), 201

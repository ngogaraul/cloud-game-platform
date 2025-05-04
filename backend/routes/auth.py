from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from models import users_collection, admins_collection

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username","").strip()
    email    = data.get("email","").strip()
    password = data.get("password","")
    is_admin = bool(data.get("is_admin", False))

    if not username or not email or not password:
        return jsonify(msg="Missing fields"), 400

    if users_collection.find_one({"email": email}):
        return jsonify(msg="Email already registered"), 409

    pw_hash = generate_password_hash(password)
    result = users_collection.insert_one({
        "username": username,
        "email": email,
        "password": pw_hash,
        "is_admin": is_admin
    })

    # mirror in admins collection
    if is_admin:
        admins_collection.insert_one({"user_id": result.inserted_id})

    token = create_access_token(
        identity=str(result.inserted_id),
        additional_claims={"is_admin": is_admin}
    )
    return jsonify(msg="User registered successfully", token=token), 201

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email    = data.get("email","").strip()
    password = data.get("password","")

    user = users_collection.find_one({"email": email})
    if not user or not check_password_hash(user["password"], password):
        return jsonify(msg="Bad credentials"), 401

    token = create_access_token(
        identity=str(user["_id"]),
        additional_claims={"is_admin": user.get("is_admin", False)}
    )
    return jsonify(msg="Login successful", token=token), 200

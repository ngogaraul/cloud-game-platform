from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
import os

load_dotenv()
app = Flask(__name__)
CORS(app)
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET")
JWTManager(app)

# ensure db & collections exist
from db import db

# register routes
from routes.auth  import auth_bp
from routes.user  import user_bp
from routes.admin import admin_bp

app.register_blueprint(auth_bp,  url_prefix="/api")
app.register_blueprint(user_bp,  url_prefix="/api")
app.register_blueprint(admin_bp, url_prefix="/api")

@app.route("/")
def index():
    return {"msg": "Cloud Game Platform API Running"}

if __name__ == "__main__":
    app.run(debug=True)

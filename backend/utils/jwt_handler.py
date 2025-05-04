from flask import abort
from flask_jwt_extended import verify_jwt_in_request, get_jwt

def admin_required(fn):
    """Decorator: allow access only if JWT has claim is_admin=True."""
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()
        if not claims.get("is_admin", False):
            abort(403, "Admin privilege required")
        return fn(*args, **kwargs)
    wrapper.__name__ = fn.__name__
    return wrapper

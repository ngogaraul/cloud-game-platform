from models import ratings_collection

def calculate_average_rating(game_id: str) -> float | None:
    """Compute the mean of all ratings for a given game_id."""
    cursor = ratings_collection.find({"game_id": game_id})
    ratings = [r["rating"] for r in cursor]
    if not ratings:
        return None
    return sum(ratings) / len(ratings)

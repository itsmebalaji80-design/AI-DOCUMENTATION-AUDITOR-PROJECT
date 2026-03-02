from fastapi import FastAPI

app = FastAPI(title="Sample API")


@app.get("/users")
def list_users():
    """
    List users.
    """
    return [{"id": 1, "name": "Asha"}, {"id": 2, "name": "Ravi"}]


@app.get("/users/{user_id}")
def get_user(user_id: int):
    """
    Get user by id.
    """
    return {"id": user_id, "name": "Asha"}


@app.post("/users")
def create_user(payload: dict):
    # Intentionally under-documented vs docs to trigger a gap.
    return {"id": 3, **payload}


@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    # Intentionally undocumented in the docs to trigger a gap.
    return {"deleted": True, "id": user_id}


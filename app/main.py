import os

import psycopg
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, ConfigDict

app = FastAPI(title="Docker Containerization Lab", version="0.1.0")


class ItemCreate(BaseModel):
    name: str


class Item(ItemCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int


def database_url() -> str:
    value = os.environ.get("DATABASE_URL")
    if not value:
        raise RuntimeError("DATABASE_URL is required")
    return value


@app.get("/livez")
def livez() -> dict[str, str]:
    return {"status": "live"}


@app.get("/readyz")
def readyz() -> dict[str, str]:
    try:
        with psycopg.connect(database_url(), connect_timeout=1) as connection:
            connection.execute("SELECT 1")
    except (psycopg.Error, RuntimeError) as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="database unavailable",
        ) from error
    return {"status": "ready"}


@app.post("/items", response_model=Item, status_code=status.HTTP_201_CREATED)
def create_item(payload: ItemCreate) -> Item:
    with psycopg.connect(database_url()) as connection:
        row = connection.execute(
            "INSERT INTO items (name) VALUES (%s) RETURNING id, name",
            (payload.name,),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=500, detail="insert returned no row")
    return Item(id=row[0], name=row[1])


@app.get("/items", response_model=list[Item])
def list_items() -> list[Item]:
    with psycopg.connect(database_url()) as connection:
        rows = connection.execute("SELECT id, name FROM items ORDER BY id").fetchall()
    return [Item(id=row[0], name=row[1]) for row in rows]

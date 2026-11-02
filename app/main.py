"""FastAPI application exposing user registration and lookup."""

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session

from app import crud
from app.database import Base, engine, get_db
from app.schemas import UserCreate, UserLogin, UserRead


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Create the tables on startup (no migrations tool in this project yet).
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Secure User Model", version="1.0.0", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_user(user_in: UserCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_user(db, user_in)
    except crud.DuplicateUserError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@app.get("/users/{user_id}", response_model=UserRead)
def read_user(user_id: int, db: Session = Depends(get_db)):
    user = crud.get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@app.post("/users/verify", response_model=UserRead)
def verify_credentials(credentials: UserLogin, db: Session = Depends(get_db)):
    user = crud.authenticate_user(db, credentials.username, credentials.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password"
        )
    return user

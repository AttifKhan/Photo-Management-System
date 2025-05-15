import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.db.engine import Base, engine
from app.routers import (
    auth,
    photo,
    follow,
    comment,
    rating,
    search,
    best_photo,
    suggestion,
    analytics,
    admin,
    
)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Photo Management App")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "*")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory="app/static/uploads"), name="uploads")

app.include_router(auth.router)
app.include_router(photo.router)
app.include_router(follow.router)
app.include_router(comment.router)
app.include_router(rating.router)
app.include_router(search.router)
app.include_router(best_photo.router)
app.include_router(suggestion.router)
app.include_router(analytics.router)
app.include_router(admin.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Photo Management App"}

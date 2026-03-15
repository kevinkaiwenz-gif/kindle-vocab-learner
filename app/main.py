"""Kindle Vocab Learner - Main application."""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.database import init_db
from app.routers import import_router, review_router, words
from app.templating import templates

app = FastAPI(title="Kindle Vocab Learner")

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include routers
app.include_router(import_router.router)
app.include_router(words.router)
app.include_router(review_router.router)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@app.get("/favicon.ico")
def favicon():
    return RedirectResponse("/static/favicon.ico", status_code=301)

"""Routes for daily review functionality."""

from datetime import datetime

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse

from app.database import get_db
from app.review import FORGOT, REMEMBERED, UNSURE, calculate_next_review
from app.templating import templates

router = APIRouter(prefix="/review", tags=["review"])


@router.get("", response_class=HTMLResponse)
def review_page(request: Request):
    """Show the daily review page."""
    db = get_db()
    try:
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        # Get words due for review
        due_words = db.execute(
            """
            SELECT w.id, w.word, w.stem, w.usage, w.interval_days,
                   w.repetitions, w.next_review,
                   b.title as book_title
            FROM words w
            LEFT JOIN books b ON w.book_id = b.id
            WHERE w.next_review <= ?
            ORDER BY w.next_review ASC
            """,
            (now,),
        ).fetchall()

        total_due = len(due_words)
        current_word = due_words[0] if due_words else None

        return templates.TemplateResponse(
            "review.html",
            {
                "request": request,
                "current_word": current_word,
                "total_due": total_due,
                "reviewed_count": 0,
            },
        )
    finally:
        db.close()


@router.post("/answer", response_class=HTMLResponse)
def submit_answer(
    request: Request,
    word_id: int = Form(...),
    quality: int = Form(...),
    reviewed_count: int = Form(0),
):
    """Process a review answer and show the next word."""
    quality_map = {0: FORGOT, 1: UNSURE, 2: REMEMBERED}
    quality_value = quality_map.get(quality, FORGOT)

    db = get_db()
    try:
        # Get current word state
        word = db.execute(
            "SELECT ease_factor, interval_days, repetitions FROM words WHERE id = ?",
            (word_id,),
        ).fetchone()

        if word:
            new_ease, new_interval, new_reps, next_review = calculate_next_review(
                quality_value,
                word["ease_factor"],
                word["interval_days"],
                word["repetitions"],
            )

            db.execute(
                """
                UPDATE words
                SET ease_factor = ?,
                    interval_days = ?,
                    repetitions = ?,
                    next_review = ?,
                    last_reviewed = datetime('now')
                WHERE id = ?
                """,
                (new_ease, new_interval, new_reps, next_review, word_id),
            )
            db.commit()

        reviewed_count += 1

        # Get next word due for review
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        due_words = db.execute(
            """
            SELECT w.id, w.word, w.stem, w.usage, w.interval_days,
                   w.repetitions, w.next_review,
                   b.title as book_title
            FROM words w
            LEFT JOIN books b ON w.book_id = b.id
            WHERE w.next_review <= ?
            ORDER BY w.next_review ASC
            """,
            (now,),
        ).fetchall()

        total_due = len(due_words)
        current_word = due_words[0] if due_words else None

        return templates.TemplateResponse(
            "partials/review_card.html",
            {
                "request": request,
                "current_word": current_word,
                "total_due": total_due,
                "reviewed_count": reviewed_count,
            },
        )
    finally:
        db.close()


@router.get("/stats", response_class=HTMLResponse)
def review_stats(request: Request):
    """Get review statistics."""
    db = get_db()
    try:
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        stats = {
            "total_words": db.execute("SELECT COUNT(*) as cnt FROM words").fetchone()["cnt"],
            "due_today": db.execute(
                "SELECT COUNT(*) as cnt FROM words WHERE next_review <= ?", (now,)
            ).fetchone()["cnt"],
            "mastered": db.execute(
                "SELECT COUNT(*) as cnt FROM words WHERE repetitions >= 5"
            ).fetchone()["cnt"],
            "learning": db.execute(
                "SELECT COUNT(*) as cnt FROM words WHERE repetitions > 0 AND repetitions < 5"
            ).fetchone()["cnt"],
            "new": db.execute(
                "SELECT COUNT(*) as cnt FROM words WHERE repetitions = 0"
            ).fetchone()["cnt"],
        }

        return templates.TemplateResponse(
            "partials/review_stats.html",
            {"request": request, "stats": stats},
        )
    finally:
        db.close()

"""Routes for word list and detail views."""

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse

from app.database import get_db
from app.templating import templates

router = APIRouter(prefix="/words", tags=["words"])

PAGE_SIZE = 20


@router.get("", response_class=HTMLResponse)
def word_list(
    request: Request,
    page: int = Query(1, ge=1),
    search: str = Query("", alias="q"),
    book_id: int | None = Query(None),
):
    """Display word list with pagination, search, and book filter."""
    db = get_db()
    try:
        offset = (page - 1) * PAGE_SIZE

        # Build query
        conditions = []
        params: list = []

        if search:
            conditions.append("(w.word LIKE ? OR w.stem LIKE ?)")
            params.extend([f"%{search}%", f"%{search}%"])

        if book_id is not None:
            conditions.append("w.book_id = ?")
            params.append(book_id)

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        # Get total count
        total = db.execute(
            f"SELECT COUNT(*) as cnt FROM words w {where_clause}", params
        ).fetchone()["cnt"]

        # Get words
        words = db.execute(
            f"""
            SELECT w.id, w.word, w.stem, w.usage, w.lookup_time, w.lookup_count,
                   w.next_review, w.interval_days, w.repetitions,
                   b.title as book_title
            FROM words w
            LEFT JOIN books b ON w.book_id = b.id
            {where_clause}
            ORDER BY w.lookup_time DESC
            LIMIT ? OFFSET ?
            """,
            params + [PAGE_SIZE, offset],
        ).fetchall()

        # Get all books for filter dropdown
        books = db.execute("SELECT id, title FROM books ORDER BY title").fetchall()

        total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)

        # Check if HTMX request for partial update
        is_htmx = request.headers.get("HX-Request") == "true"

        template = "partials/word_table.html" if is_htmx else "word_list.html"

        return templates.TemplateResponse(
            template,
            {
                "request": request,
                "words": words,
                "books": books,
                "page": page,
                "total_pages": total_pages,
                "total": total,
                "search": search,
                "book_id": book_id,
            },
        )
    finally:
        db.close()


@router.get("/{word_id}", response_class=HTMLResponse)
def word_detail(request: Request, word_id: int):
    """Display detailed view of a single word."""
    db = get_db()
    try:
        word = db.execute(
            """
            SELECT w.*, b.title as book_title, b.authors as book_authors
            FROM words w
            LEFT JOIN books b ON w.book_id = b.id
            WHERE w.id = ?
            """,
            (word_id,),
        ).fetchone()

        if not word:
            return HTMLResponse("<h2>Word not found</h2>", status_code=404)

        return templates.TemplateResponse(
            "word_detail.html",
            {"request": request, "word": word},
        )
    finally:
        db.close()

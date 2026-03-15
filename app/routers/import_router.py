"""Routes for importing Kindle vocab.db files."""

import os
import tempfile

from fastapi import APIRouter, File, Request, UploadFile
from fastapi.responses import HTMLResponse

from app.database import get_db
from app.parser import parse_vocab_db
from app.templating import templates

router = APIRouter(prefix="/import", tags=["import"])


@router.get("", response_class=HTMLResponse)
def import_page(request: Request):
    return templates.TemplateResponse("import.html", {"request": request})


@router.post("", response_class=HTMLResponse)
async def upload_vocab_db(request: Request, file: UploadFile = File(...)):
    """Upload and process a Kindle vocab.db file."""
    if not file.filename or not file.filename.endswith(".db"):
        return templates.TemplateResponse(
            "partials/import_result.html",
            {"request": request, "error": "Please upload a valid .db file."},
        )

    # Save uploaded file to temp location
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".db")
    try:
        content = await file.read()
        os.write(tmp_fd, content)
        os.close(tmp_fd)

        # Parse vocab.db
        entries = parse_vocab_db(tmp_path)
        if not entries:
            return templates.TemplateResponse(
                "partials/import_result.html",
                {"request": request, "error": "No vocabulary entries found in the file."},
            )

        # Save to our database
        db = get_db()
        try:
            imported_count = 0
            skipped_count = 0

            for entry in entries:
                # Insert or get book
                existing_book = db.execute(
                    "SELECT id FROM books WHERE title = ? AND COALESCE(asin, '') = ?",
                    (entry.book_title, entry.book_asin),
                ).fetchone()

                if existing_book:
                    book_id = existing_book["id"]
                else:
                    cursor = db.execute(
                        "INSERT INTO books (asin, title, authors, lang) VALUES (?, ?, ?, ?)",
                        (entry.book_asin, entry.book_title, entry.book_authors, entry.book_lang),
                    )
                    book_id = cursor.lastrowid

                # Insert word (skip if duplicate)
                try:
                    db.execute(
                        """
                        INSERT INTO words (word, stem, lang, book_id, usage, lookup_time,
                                           lookup_count, next_review)
                        VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
                        """,
                        (
                            entry.word,
                            entry.stem,
                            entry.book_lang,
                            book_id,
                            entry.usage,
                            entry.lookup_time,
                            entry.lookup_count,
                        ),
                    )
                    imported_count += 1
                except Exception:
                    skipped_count += 1

            db.commit()

            return templates.TemplateResponse(
                "partials/import_result.html",
                {
                    "request": request,
                    "success": True,
                    "imported": imported_count,
                    "skipped": skipped_count,
                    "total": len(entries),
                },
            )
        finally:
            db.close()

    except Exception as e:
        return templates.TemplateResponse(
            "partials/import_result.html",
            {"request": request, "error": f"Error processing file: {e}"},
        )
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

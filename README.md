# Kindle Vocab Learner

A local web application that turns your Kindle Vocabulary Builder into a spaced repetition learning tool.

## Features

- **Import** — Upload your Kindle `vocab.db` file to extract vocabulary
- **Word List** — Browse, search, and filter all imported words with pagination
- **Word Detail** — View word context, book info, and review status
- **Daily Review** — Practice with spaced repetition (SM-2 algorithm)

## Tech Stack

| Layer    | Technology         |
|----------|--------------------|
| Backend  | Python + FastAPI   |
| Database | SQLite             |
| Frontend | HTML + HTMX + Jinja2 |

## Project Structure

```
kindle-vocab-learner/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── database.py           # SQLite database initialization
│   ├── parser.py             # Kindle vocab.db parser
│   ├── review.py             # Spaced repetition algorithm (SM-2)
│   ├── routers/
│   │   ├── import_router.py  # Import page & upload handler
│   │   ├── words.py          # Word list & detail views
│   │   └── review_router.py  # Daily review logic
│   ├── templates/
│   │   ├── base.html         # Base layout with nav
│   │   ├── home.html         # Home page with stats
│   │   ├── import.html       # Import/upload page
│   │   ├── word_list.html    # Word list with search & filter
│   │   ├── word_detail.html  # Single word detail view
│   │   ├── review.html       # Daily review page
│   │   └── partials/         # HTMX partial templates
│   └── static/
│       └── style.css         # Application styles
├── data/                     # SQLite database storage
├── pyproject.toml            # Python dependencies
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.11+
- [Poetry](https://python-poetry.org/)

### Installation

```bash
# Clone and enter the project
cd kindle-vocab-learner

# Install dependencies
poetry install

# Run the development server
poetry run fastapi dev app/main.py
```

Open http://localhost:8000 in your browser.

### Usage

1. **Get your vocab.db** — Connect your Kindle via USB, find the file at:
   ```
   Kindle/system/vocabulary/vocab.db
   ```

2. **Import** — Go to the Import page and upload your `vocab.db` file.

3. **Browse** — View all imported words in the Word List. Search by word or filter by book.

4. **Review** — Start a Daily Review session. For each word:
   - A sentence from your book is displayed
   - Click "Show Answer" to reveal the word
   - Rate yourself: **Remembered**, **Unsure**, or **Forgot**
   - The system adjusts the next review time accordingly

## Spaced Repetition Algorithm

Uses a simplified SM-2 algorithm:

| Response     | Effect                                      |
|--------------|---------------------------------------------|
| Remembered   | Increase interval (×ease factor), ease +0.1 |
| Unsure       | Reduce interval (×0.6), ease −0.15          |
| Forgot       | Reset to 10 minutes, ease −0.3              |

Words progress through stages: **New** → **Learning** → **Mastered** (5+ successful repetitions).

# Course Catalog API

A standalone FastAPI backend for the six-course catalog, with filtering, sorting, pagination, and interactive API documentation.

## Run locally

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
fastapi dev main.py
```

Open <http://127.0.0.1:8000/docs> for the interactive documentation.

## What was verified

- `GET /` returns `{"message":"Course Catalog API is running"}`.
- `GET /courses` returns all six courses, ordered by likes with `ai-integration` first.
- `GET /courses?is_elective=true` returns `ai-integration` and `api-design`; `false` returns the four required courses.
- `GET /courses?sort=title` sorts the courses alphabetically by title.
- `GET /courses?page=2&page_size=2` returns `web-security` and `backend-fastapi`.
- `GET /courses/web-security` returns that course; `GET /courses/nope` returns 404 with `{"detail":"Course not found"}`.
- `GET /docs`, `/redoc`, and `/openapi.json` expose the generated API documentation and schema.

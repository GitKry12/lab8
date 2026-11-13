"""Print SQL statement counts for two nested GraphQL queries."""
import os

import httpx

QUERIES = [
    ("students -> enrollments -> course", "{ students { name enrollments { course { title } } } }"),
    ("enrollments -> course, student", "{ enrollments { id course { title } student { name } } }"),
]


def main() -> None:
    with httpx.Client(base_url=os.getenv("API_BASE_URL", "http://127.0.0.1:8000"), trust_env=False) as client:
        for title, query in QUERIES:
            response = client.post("/graphql", json={"query": query})
            response.raise_for_status()
            body = response.json()
            if body.get("errors"):
                raise RuntimeError(body["errors"])
            rows = len(next(iter(body["data"].values())))
            print(f"{title:<34} rows: {rows:<3} SQL queries: {response.headers['x-sql-queries']}")


if __name__ == "__main__":
    main()

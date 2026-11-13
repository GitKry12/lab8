"""Check the five REST error contracts on the seed data."""
import os

import httpx

CASES = [
    ("email already taken", "/students", {"name": "Aigerim Two", "email": "aigerim@example.com"}, 409, "email-taken"),
    ("already enrolled", "/enrollments", {"courseId": "ai-integration", "studentId": 3}, 409, "already-enrolled"),
    ("unknown course", "/enrollments", {"courseId": "nope", "studentId": 3}, 404, "course-not-found"),
    ("unknown student", "/enrollments", {"courseId": "web-security", "studentId": 999}, 404, "student-not-found"),
    ("name too short", "/students", {"name": "N", "email": "short@example.com"}, 422, None),
]


def main() -> int:
    passed = 0
    with httpx.Client(base_url=os.getenv("API_BASE_URL", "http://127.0.0.1:8000"), trust_env=False) as client:
        for name, route, body, expected, slug in CASES:
            response = client.post(route, json=body)
            payload = response.json()
            kind = payload.get("type", "-").rsplit("/", 1)[-1]
            content_type = response.headers["content-type"].split(";")[0]
            ok = response.status_code == expected
            if slug:
                ok = ok and kind == slug and content_type == "application/problem+json"
                ok = ok and payload["status"] == expected and payload["instance"] == route
            else:
                ok = ok and content_type == "application/json" and bool(payload.get("detail"))
            passed += int(ok)
            print(f"{'ok' if ok else 'FAIL'}  {name}: {response.status_code} {content_type} {kind}")
    print(f"{passed} of {len(CASES)} as expected")
    return int(passed != len(CASES))


if __name__ == "__main__":
    raise SystemExit(main())

"""Check the five expected HTTP errors against a running API with seed data."""
import os

import httpx

CASES = [
    ("email already taken", "/students", {"name": "Aigerim Two", "email": "aigerim@example.com"}, 409),
    ("already enrolled", "/enrollments", {"courseId": "ai-integration", "studentId": 3}, 409),
    ("unknown course", "/enrollments", {"courseId": "nope", "studentId": 3}, 404),
    ("unknown student", "/enrollments", {"courseId": "web-security", "studentId": 999}, 404),
    ("name too short", "/students", {"name": "N", "email": "short@example.com"}, 422),
]


if __name__ == "__main__":
    passed = 0
    with httpx.Client(base_url=os.getenv("API_BASE_URL", "http://127.0.0.1:8000"), trust_env=False) as client:
        for name, route, body, expected in CASES:
            response = client.post(route, json=body)
            ok = response.status_code == expected
            passed += int(ok)
            print(f"{'ok' if ok else 'FAIL'}  {name}: {response.status_code} {response.text[:80]}")
    print(f"{passed} of {len(CASES)} as expected")
    raise SystemExit(int(passed != len(CASES)))

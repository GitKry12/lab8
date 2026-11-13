"""Verify dangerous GraphQL queries are rejected and internal errors are masked."""
import argparse
import os

import httpx

CYCLE = 'query Cycle { student(id: 2) { enrollments { student { enrollments { student { enrollments { id } } } } } } }'
ALIASES = "{ " + " ".join(f'a{i}: course(id: "api-design") {{ title }}' for i in range(1, 13)) + " }"
CASES = [
    ("depth 6", CYCLE, "exceeds maximum operation depth"),
    ("12 aliases", ALIASES, "12 aliases found. Allowed: 10"),
    ("negative limit", "{ courses(limit: -1) { id } }", "limit must be between 1 and 100"),
    ("non-numeric ID", '{ student(id: "abc") { name } }', "Invalid ID: 'abc'"),
    ("bigint overflow", '{ student(id: "99999999999999999999") { name } }', "Unexpected error."),
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--introspection-off", action="store_true")
    args = parser.parse_args()
    cases = [*CASES, ("introspection", "{ __schema { queryType { name } } }",
                      "introspection has been disabled" if args.introspection_off else None)]
    passed = 0
    with httpx.Client(base_url=os.getenv("API_BASE_URL", "http://127.0.0.1:8000"), trust_env=False) as client:
        for title, query, expected in cases:
            response = client.post("/graphql", json={"query": query})
            body = response.json()
            messages = [error["message"] for error in body.get("errors", [])]
            ok = response.status_code == 200 and (any(expected in msg for msg in messages) if expected else not messages)
            passed += int(ok)
            print(f"{'ok' if ok else 'FAIL'}  {title}: {response.status_code} {messages[0] if messages else 'data, no errors'}")
    print(f"{passed} of {len(cases)} as expected")
    return int(passed != len(cases))


if __name__ == "__main__":
    raise SystemExit(main())

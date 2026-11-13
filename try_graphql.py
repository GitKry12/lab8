"""Eight query and rule-error checks; these do not add seed rows."""
import os

import httpx


def enroll(course_id: str, student_id: str) -> str:
    return ('mutation { enroll(input: {courseId: "' + course_id + '", studentId: "'
            + student_id + '"}) { enrollment { id } userErrors { code } } }')


CASES = [
    ("courses(limit: 2)", "{ courses(limit: 2) { id } }",
     lambda d: ",".join(c["id"] for c in d["data"]["courses"]), "ai-integration,modern-frontend"),
    ("existing course", '{ course(id: "api-design") { title } }',
     lambda d: d["data"]["course"]["title"], "API Design: REST vs GraphQL"),
    ("unknown course", '{ course(id: "nope") { title } }',
     lambda d: str(d["data"]["course"]), "None"),
    ("student 2 courses", "{ student(id: 2) { enrollments { course { id } } } }",
     lambda d: str(len(d["data"]["student"]["enrollments"])), "3"),
    ("duplicate enrollment", enroll("ai-integration", "3"),
     lambda d: d["data"]["enroll"]["userErrors"][0]["code"], "ALREADY_ENROLLED"),
    ("unknown course enrollment", enroll("nope", "3"),
     lambda d: d["data"]["enroll"]["userErrors"][0]["code"], "COURSE_NOT_FOUND"),
    ("unknown student enrollment", enroll("web-security", "999"),
     lambda d: d["data"]["enroll"]["userErrors"][0]["code"], "STUDENT_NOT_FOUND"),
    ("unknown field", '{ course(id: "api-design") { titel } }',
     lambda d: d["errors"][0]["message"].split(". Did you")[0].rstrip("."),
     "Cannot query field 'titel' on type 'Course'"),
]


def main() -> int:
    passed = 0
    with httpx.Client(base_url=os.getenv("API_BASE_URL", "http://127.0.0.1:8000"), trust_env=False) as client:
        for title, query, pick, expected in CASES:
            response = client.post("/graphql", json={"query": query})
            body = response.json()
            try:
                actual = pick(body)
            except (KeyError, IndexError, TypeError):
                actual = str(body)
            ok = response.status_code == 200 and actual == expected
            if title != "unknown field":
                ok = ok and not body.get("errors")
            passed += int(ok)
            print(f"{'ok' if ok else 'FAIL'}  {title}: {actual}")
    print(f"{passed} of {len(CASES)} as expected")
    return int(passed != len(CASES))


if __name__ == "__main__":
    raise SystemExit(main())

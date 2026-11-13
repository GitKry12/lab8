"""One POST with twelve mutation aliases; protected server executes zero SQL."""
import os

import httpx

QUERY = "mutation { " + " ".join(
    f'a{i}: likeCourse(id: "api-design") {{ course {{ likes }} }}' for i in range(1, 13)
) + " }"


if __name__ == "__main__":
    with httpx.Client(base_url=os.getenv("API_BASE_URL", "http://127.0.0.1:8000"), trust_env=False) as client:
        response = client.post("/graphql", json={"query": QUERY})
    body = response.json()
    print("HTTP status:", response.status_code)
    if body.get("errors"):
        print("error:", body["errors"][0]["message"])
    else:
        print("likes:", [body["data"][f"a{i}"]["course"]["likes"] for i in range(1, 13)])
    print("SQL queries:", response.headers["x-sql-queries"])
    ok = response.status_code == 200 and response.headers["x-sql-queries"] == "0"
    ok = ok and any("12 aliases found" in e["message"] for e in body.get("errors", []))
    raise SystemExit(int(not ok))

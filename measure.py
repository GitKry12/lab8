"""Measure equivalent My courses screens by HTTP requests, rounds, bytes and SQL."""
import asyncio
import json
import os
import sys

import httpx

STUDENT = 2
MY_COURSES = """
query MyCourses($id: ID!) {
  student(id: $id) {
    name
    enrollments { id course { title credits level } }
  }
}
"""


async def rest(client: httpx.AsyncClient):
    first = await asyncio.gather(client.get(f"/students/{STUDENT}"),
                                 client.get(f"/students/{STUDENT}/enrollments"))
    for response in first:
        response.raise_for_status()
    codes = [item["courseId"] for item in first[1].json()]
    second = await asyncio.gather(*(client.get(f"/courses/{code}") for code in codes))
    return [*first, *second], 2


async def graphql(client: httpx.AsyncClient):
    response = await client.post("/graphql", json={"query": MY_COURSES, "variables": {"id": str(STUDENT)}})
    response.raise_for_status()
    if response.json().get("errors"):
        raise RuntimeError(response.json()["errors"])
    return [response], 1


async def measure():
    result = {}
    async with httpx.AsyncClient(base_url=os.getenv("API_BASE_URL", "http://127.0.0.1:8000"), trust_env=False) as client:
        for name, run in (("REST", rest), ("GraphQL", graphql)):
            responses, rounds = await run(client)
            for response in responses:
                response.raise_for_status()
            result[name] = {"requests": len(responses), "rounds": rounds,
                            "bytes": sum(len(r.content) for r in responses),
                            "sql": sum(int(r.headers["x-sql-queries"]) for r in responses)}
            if name == "REST":
                rest_screen = {"name": responses[0].json()["name"],
                               "courses": [{key: r.json()[key] for key in ("title", "credits", "level")}
                                           for r in responses[2:]]}
            else:
                student = responses[0].json()["data"]["student"]
                graphql_screen = {"name": student["name"], "courses": [e["course"] for e in student["enrollments"]]}
                assert graphql_screen == rest_screen, "The two screens must contain identical data"
    return result


if __name__ == "__main__":
    result = asyncio.run(measure())
    if "--json" in sys.argv:
        print(json.dumps(result, indent=2))
    else:
        print(f"{'':<8} {'requests':<9} {'rounds':<7} {'bytes':<6} SQL queries")
        for name, values in result.items():
            print(f"{name:<8} {values['requests']:<9} {values['rounds']:<7} {values['bytes']:<6} {values['sql']}")

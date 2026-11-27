import json
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

HOST = "0.0.0.0"
PORT = 9100

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen2.5:3b"

KHUB_PATH = Path(
    "/projects/minibank/ai/khub/minibank-knowledge.json"
)


def load_khub():
    with KHUB_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def call_ollama(incident_context, khub):

    system_prompt = """
You are the RCA investigator for the MiniBank application.

Your job is to analyze Dynatrace incident evidence together with
MiniBank architecture and remediation knowledge.

Rules:

1. Use only the supplied evidence and knowledge.
2. Do not invent missing telemetry.
3. Distinguish symptoms from root causes.
4. Check dependencies before recommending a service restart.
5. Never generate shell commands.
6. Recommend only an action present in allowed_actions.
7. If evidence is insufficient or conflicting, recommend ESCALATE.
8. Return ONLY valid JSON.

Required output:

{
  "root_cause": "string",
  "evidence": ["string"],
  "recommended_action": "string",
  "reason": "string",
  "confidence": 0.0
}

confidence must be between 0.0 and 1.0.
"""

    user_prompt = f"""
DYNATRACE INCIDENT CONTEXT:

{json.dumps(incident_context, indent=2)}

MINIBANK KNOWLEDGE HUB:

{json.dumps(khub, indent=2)}

Analyze the incident and return the required RCA JSON.
"""

    payload = {
        "model": MODEL,
        "stream": False,
        "format": "json",
        "messages": [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ]
    }

    request = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json"
        },
        method="POST"
    )

    with urllib.request.urlopen(
        request,
        timeout=120
    ) as response:

        result = json.loads(
            response.read().decode("utf-8")
        )

    content = result["message"]["content"]

    return json.loads(content)


class RCAHandler(BaseHTTPRequestHandler):

    def send_json(self, status_code, body):

        response = json.dumps(
            body,
            indent=2
        ).encode("utf-8")

        self.send_response(status_code)
        self.send_header(
            "Content-Type",
            "application/json"
        )
        self.send_header(
            "Content-Length",
            str(len(response))
        )
        self.end_headers()

        self.wfile.write(response)


    def do_GET(self):

        if self.path == "/health":

            self.send_json(
                200,
                {
                    "status": "UP",
                    "service": "minibank-ai-rca",
                    "model": MODEL
                }
            )

        else:

            self.send_json(
                404,
                {"error": "Not found"}
            )


    def do_POST(self):

        if self.path != "/api/rca":

            self.send_json(
                404,
                {"error": "Not found"}
            )
            return

        try:

            content_length = int(
                self.headers.get(
                    "Content-Length",
                    "0"
                )
            )

            body = self.rfile.read(
                content_length
            )

            incident_context = json.loads(
                body.decode("utf-8")
            )

            khub = load_khub()

            rca = call_ollama(
                incident_context,
                khub
            )

            self.send_json(
                200,
                {
                    "status": "SUCCESS",
                    "model": MODEL,
                    "rca": rca
                }
            )

        except Exception as e:

            self.send_json(
                500,
                {
                    "status": "FAILED",
                    "error": str(e)
                }
            )


if __name__ == "__main__":

    print(
        f"MiniBank AI RCA service running on "
        f"http://{HOST}:{PORT}"
    )

    server = HTTPServer(
        (HOST, PORT),
        RCAHandler
    )

    server.serve_forever()

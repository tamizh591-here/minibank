from http.server import BaseHTTPRequestHandler, HTTPServer
import subprocess
import json
import os

HOST = "0.0.0.0"
PORT = 9000

RESTART_SCRIPT = "/projects/minibank/remediation/scripts/restart-customer.sh"

# POC token - we'll improve secret handling later
API_TOKEN = "minibank-selfheal-2026"


class RemediationHandler(BaseHTTPRequestHandler):

    def send_json(self, status_code, payload):
        body = json.dumps(payload).encode("utf-8")

        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()

        self.wfile.write(body)


    def do_GET(self):

        if self.path == "/health":
            self.send_json(200, {
                "status": "UP",
                "service": "minibank-remediation"
            })
            return

        self.send_json(404, {
            "error": "Not Found"
        })


    def do_POST(self):

        if self.path != "/api/remediation/customer/restart":
            self.send_json(404, {
                "error": "Not Found"
            })
            return

        auth_header = self.headers.get("Authorization")

        if auth_header != f"Bearer {API_TOKEN}":
            self.send_json(401, {
                "error": "Unauthorized"
            })
            return

        print("Customer remediation requested")

        try:

            result = subprocess.run(
                [RESTART_SCRIPT],
                capture_output=True,
                text=True,
                timeout=90
            )

            print(result.stdout)

            if result.returncode == 0:

                self.send_json(200, {
                    "status": "SUCCESS",
                    "service": "customer-service",
                    "action": "RESTART",
                    "message": "Customer Service recovered successfully"
                })

            else:

                self.send_json(500, {
                    "status": "FAILED",
                    "service": "customer-service",
                    "action": "RESTART",
                    "message": "Customer Service recovery failed",
                    "output": result.stdout
                })

        except subprocess.TimeoutExpired:

            self.send_json(504, {
                "status": "FAILED",
                "service": "customer-service",
                "message": "Remediation timed out"
            })


if __name__ == "__main__":

    if not os.path.isfile(RESTART_SCRIPT):
        raise RuntimeError(
            f"Restart script not found: {RESTART_SCRIPT}"
        )

    print(f"MiniBank Remediation API listening on port {PORT}")

    server = HTTPServer((HOST, PORT), RemediationHandler)

    server.serve_forever()

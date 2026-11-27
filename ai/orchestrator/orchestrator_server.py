import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer


# ============================================================
# Import AI Pipeline
# ============================================================

ORCHESTRATOR_PATH = "/projects/minibank/ai/orchestrator"

if ORCHESTRATOR_PATH not in sys.path:
    sys.path.insert(0, ORCHESTRATOR_PATH)

from ai_pipeline import (
    call_qwen,
    call_local_evaluator,
    run_guardrail,
    build_report
)


# ============================================================
# Configuration
# ============================================================

HOST = "0.0.0.0"
PORT = 9200


# ============================================================
# AI Pipeline
# ============================================================

def run_ai_pipeline(context):

    print()
    print("[1/4] Qwen RCA investigation...")

    qwen_result = call_qwen(
        context
    )

    print(
        "[2/4] Local AI evaluation..."
    )

    evaluator_result = call_local_evaluator(
        context,
        qwen_result
    )

    print(
        "[3/4] Deterministic guardrail..."
    )

    guardrail_result = run_guardrail(
        context,
        qwen_result,
        evaluator_result
    )

    print(
        "[4/4] Building RCA report..."
    )

    report = build_report(
        context,
        qwen_result,
        evaluator_result,
        guardrail_result
    )

    print(
        "AI analysis completed."
    )

    return report


# ============================================================
# HTTP Handler
# ============================================================

class OrchestratorHandler(BaseHTTPRequestHandler):

    def send_json(
        self,
        status_code,
        payload
    ):

        body = json.dumps(
            payload,
            indent=2
        ).encode("utf-8")

        self.send_response(
            status_code
        )

        self.send_header(
            "Content-Type",
            "application/json"
        )

        self.send_header(
            "Content-Length",
            str(len(body))
        )

        self.end_headers()

        self.wfile.write(
            body
        )


    # --------------------------------------------------------
    # GET
    # --------------------------------------------------------

    def do_GET(self):

        if self.path == "/health":

            self.send_json(
                200,
                {
                    "status": "UP",
                    "service":
                        "minibank-ai-orchestrator",
                    "investigator":
                        "qwen2.5:3b",
                    "evaluator":
                        "qwen2.5:3b-local",
                    "remediation_enabled":
                        False
                }
            )

            return

        self.send_json(
            404,
            {
                "error": "Not Found"
            }
        )


    # --------------------------------------------------------
    # POST
    # --------------------------------------------------------

    def do_POST(self):

        if self.path != "/api/analyze":

            self.send_json(
                404,
                {
                    "error": "Not Found"
                }
            )

            return

        try:

            content_length = int(
                self.headers.get(
                    "Content-Length",
                    0
                )
            )

            if content_length <= 0:

                self.send_json(
                    400,
                    {
                        "status": "ERROR",
                        "error":
                            "Request body is empty"
                    }
                )

                return


            # ------------------------------------------------
            # Read request
            # ------------------------------------------------

            body = self.rfile.read(
                content_length
            )

            context = json.loads(
                body.decode("utf-8")
            )


            # ------------------------------------------------
            # Basic contract validation
            # ------------------------------------------------

            if not isinstance(
                context,
                dict
            ):

                self.send_json(
                    400,
                    {
                        "status": "ERROR",
                        "error":
                            "AI context must be a JSON object"
                    }
                )

                return


            analysis_request = context.get(
                "analysis_request",
                {}
            )

            target_service = (
                analysis_request.get(
                    "target_service"
                )
            )

            if not target_service:

                self.send_json(
                    400,
                    {
                        "status": "ERROR",
                        "error":
                            "analysis_request.target_service "
                            "is missing"
                    }
                )

                return


            incident = context.get(
                "incident",
                {}
            )

            print()
            print("=" * 60)
            print(
                "MiniBank AI Analysis Request"
            )
            print("=" * 60)

            print(
                "Problem ID     :",
                incident.get(
                    "problem_id"
                )
            )

            print(
                "Problem        :",
                incident.get(
                    "problem_name"
                )
            )

            print(
                "Status         :",
                incident.get(
                    "status"
                )
            )

            print(
                "Target Service :",
                target_service
            )


            # ------------------------------------------------
            # Execute AI analysis
            # ------------------------------------------------

            report = run_ai_pipeline(
                context
            )


            # ------------------------------------------------
            # Return result
            # ------------------------------------------------

            self.send_json(
                200,
                {
                    "status": "SUCCESS",
                    "report": report
                }
            )


        except json.JSONDecodeError as e:

            self.send_json(
                400,
                {
                    "status": "ERROR",
                    "error":
                        f"Invalid JSON: {str(e)}"
                }
            )


        except Exception as e:

            print()
            print(
                "Pipeline failed:",
                f"{type(e).__name__}: {e}"
            )

            self.send_json(
                500,
                {
                    "status": "ERROR",
                    "error_type":
                        type(e).__name__,
                    "error":
                        str(e)
                }
            )


    # --------------------------------------------------------
    # HTTP Logging
    # --------------------------------------------------------

    def log_message(
        self,
        format,
        *args
    ):

        print(
            f"[HTTP] "
            f"{self.address_string()} "
            f"{format % args}"
        )


# ============================================================
# Main
# ============================================================

def main():

    server = HTTPServer(
        (HOST, PORT),
        OrchestratorHandler
    )

    print("=" * 60)
    print(
        "MiniBank AI Orchestrator"
    )
    print("=" * 60)

    print(
        f"Listening on {HOST}:{PORT}"
    )

    print(
        "Health  : GET  /health"
    )

    print(
        "Analyze : POST /api/analyze"
    )

    print()
    print(
        "Investigator : Qwen2.5:3B"
    )

    print(
        "Evaluator    : Qwen2.5:3B "
        "(separate local inference)"
    )

    print(
        "Guardrail    : Deterministic Python"
    )

    print()
    print(
        "IMPORTANT: Automatic remediation "
        "is DISABLED."
    )

    print("=" * 60)

    try:

        server.serve_forever()

    except KeyboardInterrupt:

        print(
            "\nStopping orchestrator..."
        )

        server.server_close()


if __name__ == "__main__":
    main()

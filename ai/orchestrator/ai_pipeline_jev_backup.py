import json
import os
import sys
import urllib.request
import urllib.error


# ============================================================
# Import Guardrail
# ============================================================

GUARDRAIL_PATH = "/projects/minibank/ai/guardrail"

if GUARDRAIL_PATH not in sys.path:
    sys.path.insert(0, GUARDRAIL_PATH)

from guardrail import evaluate


# ============================================================
# Configuration
# ============================================================

RCA_URL = "http://localhost:9100/api/rca"
JEV_URL = "https://jev-ai.pro/api/v1/systemone"

REPORT_FILE = (
    "/projects/minibank/ai/orchestrator/"
    "latest-rca-report.json"
)


# ============================================================
# Generic HTTP JSON Client
# ============================================================

def post_json(url, payload, headers=None, timeout=180):

    request_headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "MiniBank-AIOps-POC/1.0"
    }

    if headers:
        request_headers.update(headers)

    request = urllib.request.Request(
        url=url,
        data=json.dumps(payload).encode("utf-8"),
        headers=request_headers,
        method="POST"
    )

    try:

        with urllib.request.urlopen(
            request,
            timeout=timeout
        ) as response:

            response_body = response.read().decode("utf-8")

            return json.loads(response_body)

    except urllib.error.HTTPError as e:

        error_body = e.read().decode(
            "utf-8",
            errors="replace"
        )

        raise RuntimeError(
            f"HTTP {e.code} from {url}\n"
            f"Response: {error_body}"
        ) from e

    except urllib.error.URLError as e:

        raise RuntimeError(
            f"Unable to connect to {url}: {e.reason}"
        ) from e


# ============================================================
# STEP 1 - Qwen RCA
# ============================================================

def call_qwen(context):

    result = post_json(
        RCA_URL,
        context,
        timeout=180
    )

    if result.get("status") != "SUCCESS":

        raise RuntimeError(
            f"RCA service failed: {result}"
        )

    if "rca" not in result:

        raise RuntimeError(
            "RCA service response does not contain 'rca'"
        )

    return result["rca"]


# ============================================================
# STEP 2 - Jev Evaluation
# ============================================================

def call_jev(context, qwen_result):

    api_key = os.getenv("JEV_AI_API_KEY")

    if not api_key:

        raise RuntimeError(
            "JEV_AI_API_KEY is not configured"
        )

    incident = context.get(
        "incident",
        {}
    )

    infrastructure = context.get(
        "infrastructure_evidence",
        {}
    )

    logs = context.get(
        "log_evidence",
        []
    )

    traces = context.get(
        "trace_evidence",
        []
    )

    payload = {

        "model": "jev-latest",

        "state": {

            "incident": incident,

            "infrastructure_evidence": infrastructure,

            "log_evidence": logs,

            "trace_evidence": traces,

            "qwen_root_cause": qwen_result.get(
                "root_cause"
            ),

            "qwen_evidence": qwen_result.get(
                "evidence",
                []
            ),

            "qwen_recommended_action": qwen_result.get(
                "recommended_action"
            ),

            "qwen_reason": qwen_result.get(
                "reason"
            ),

            "qwen_confidence": qwen_result.get(
                "confidence"
            )
        },

        "questions": {

            "rca_support": {

                "type": "choice",

                "instructions": (
                    "Based only on the supplied incident "
                    "evidence, determine whether Qwen's "
                    "proposed root cause is supported."
                ),

                "criteria": {

                    "supported": (
                        "The supplied evidence directly "
                        "supports the proposed root cause."
                    ),

                    "contradicted": (
                        "The supplied evidence conflicts "
                        "with the proposed root cause."
                    ),

                    "insufficient_evidence": (
                        "The supplied evidence does not "
                        "establish the proposed root cause."
                    )
                }
            },

            "action_support": {

                "type": "choice",

                "instructions": (
                    "Based only on the supplied evidence, "
                    "determine whether Qwen's proposed "
                    "remediation action is sufficiently "
                    "supported for automatic remediation."
                ),

                "criteria": {

                    "supported": (
                        "There is sufficient evidence for "
                        "the proposed automatic action."
                    ),

                    "not_supported": (
                        "The supplied evidence argues "
                        "against the proposed automatic action."
                    ),

                    "needs_review": (
                        "There is insufficient evidence to "
                        "safely approve the proposed action."
                    )
                }
            }
        }
    }

    result = post_json(
        JEV_URL,
        payload,
        headers={
            "Authorization": f"Bearer {api_key}"
        },
        timeout=180
    )

    if "answers" not in result:

        raise RuntimeError(
            f"Jev response does not contain answers: {result}"
        )

    return {
        "model": result.get("model"),
        "answers": result["answers"],
        "usage": result.get("usage", {})
    }


# ============================================================
# STEP 3 - Guardrail
# ============================================================

def run_guardrail(
    context,
    qwen_result,
    jev_result
):

    target_service = (
        context
        .get("analysis_request", {})
        .get("target_service")
    )

    if not target_service:

        raise RuntimeError(
            "target_service missing from analysis_request"
        )

    answers = jev_result.get(
        "answers",
        {}
    )

    return evaluate(
        qwen_result,
        answers,
        target_service
    )


# ============================================================
# STEP 4 - Human / Machine Report
# ============================================================

def build_report(
    context,
    qwen_result,
    jev_result,
    guardrail_result
):

    incident = context.get(
        "incident",
        {}
    )

    return {

        "report_version": "1.0",

        "title": "MiniBank AI Incident Analysis",

        "incident": {

            "problem_id": incident.get(
                "problem_id"
            ),

            "problem_name": incident.get(
                "problem_name"
            ),

            "status": incident.get(
                "status"
            ),

            "category": incident.get(
                "category"
            ),

            "description": incident.get(
                "description"
            ),

            "affected_entities": incident.get(
                "affected_entities",
                []
            )
        },

        "qwen_analysis": {

            "root_cause": qwen_result.get(
                "root_cause"
            ),

            "evidence": qwen_result.get(
                "evidence",
                []
            ),

            "recommended_action": qwen_result.get(
                "recommended_action"
            ),

            "reason": qwen_result.get(
                "reason"
            ),

            "confidence": qwen_result.get(
                "confidence"
            )
        },

        "jev_validation": {

            "model": jev_result.get(
                "model"
            ),

            "rca": (
                jev_result
                .get("answers", {})
                .get("rca_support", {})
            ),

            "action": (
                jev_result
                .get("answers", {})
                .get("action_support", {})
            ),

            "usage": jev_result.get(
                "usage",
                {}
            )
        },

        "final_decision": {

            "decision": guardrail_result.get(
                "decision"
            ),

            "approved_action": guardrail_result.get(
                "approved_action"
            ),

            "reason": guardrail_result.get(
                "reason"
            ),

            "validation": guardrail_result.get(
                "validation",
                {}
            )
        }
    }


# ============================================================
# Formatting Helpers
# ============================================================

def format_percent(value):

    if value is None:
        return "N/A"

    try:
        return f"{float(value) * 100:.1f}%"

    except (TypeError, ValueError):
        return str(value)


def print_probability_table(probabilities):

    if not probabilities:
        print("  No probability information returned.")
        return

    for name, probability in probabilities.items():

        print(
            f"  {name:<24} "
            f"{format_percent(probability)}"
        )


def print_report(report):

    incident = report[
        "incident"
    ]

    qwen = report[
        "qwen_analysis"
    ]

    jev = report[
        "jev_validation"
    ]

    decision = report[
        "final_decision"
    ]

    print()
    print("=" * 70)
    print("              MINIBANK AI INCIDENT ANALYSIS")
    print("=" * 70)

    print()
    print("INCIDENT")
    print("-" * 70)

    print(
        f"Problem ID       : "
        f"{incident.get('problem_id')}"
    )

    print(
        f"Problem          : "
        f"{incident.get('problem_name')}"
    )

    print(
        f"Status           : "
        f"{incident.get('status')}"
    )

    print(
        f"Category         : "
        f"{incident.get('category')}"
    )

    affected = incident.get(
        "affected_entities",
        []
    )

    print(
        f"Affected Service : "
        f"{', '.join(affected) if affected else 'N/A'}"
    )

    print()
    print("QWEN INVESTIGATION")
    print("-" * 70)

    print(
        f"Proposed RCA     : "
        f"{qwen.get('root_cause')}"
    )

    print(
        f"Qwen Confidence  : "
        f"{format_percent(qwen.get('confidence'))}"
    )

    print(
        f"Proposed Action  : "
        f"{qwen.get('recommended_action')}"
    )

    print()
    print("Evidence:")

    evidence = qwen.get(
        "evidence",
        []
    )

    if evidence:

        for item in evidence:
            print(f"  - {item}")

    else:
        print("  - No evidence supplied by Qwen.")

    print()
    print("Qwen Reasoning:")

    print(
        f"  {qwen.get('reason')}"
    )

    print()
    print("JEV INDEPENDENT VALIDATION")
    print("-" * 70)

    print(
        f"Jev Model        : "
        f"{jev.get('model')}"
    )

    rca = jev.get(
        "rca",
        {}
    )

    print(
        f"RCA Evaluation   : "
        f"{str(rca.get('choice')).upper()}"
    )

    print(
        f"RCA Confidence   : "
        f"{format_percent(rca.get('confidence'))}"
    )

    print("RCA Probabilities:")

    print_probability_table(
        rca.get(
            "probabilities",
            {}
        )
    )

    print()

    action = jev.get(
        "action",
        {}
    )

    print(
        f"Action Evaluation: "
        f"{str(action.get('choice')).upper()}"
    )

    print(
        f"Action Confidence: "
        f"{format_percent(action.get('confidence'))}"
    )

    print("Action Probabilities:")

    print_probability_table(
        action.get(
            "probabilities",
            {}
        )
    )

    print()
    print("FINAL GUARDRAIL DECISION")
    print("-" * 70)

    final_decision = decision.get(
        "decision"
    )

    if final_decision == "APPROVE":
        display_decision = "APPROVED"

    elif final_decision == "NO_ACTION":
        display_decision = "NO ACTION REQUIRED"

    elif final_decision == "ESCALATE":
        display_decision = "ESCALATE / HUMAN REVIEW"

    elif final_decision == "REJECT":
        display_decision = "REJECTED"

    else:
        display_decision = str(
            final_decision
        )

    print(
        f"Decision         : "
        f"{display_decision}"
    )

    print(
        f"Approved Action  : "
        f"{decision.get('approved_action')}"
    )

    print(
        f"Reason           : "
        f"{decision.get('reason')}"
    )

    print()
    print("=" * 70)


# ============================================================
# Main Pipeline
# ============================================================

def main():

    if len(sys.argv) != 2:

        print(
            "Usage:\n"
            "  python3 ai_pipeline.py "
            "<incident-context.json>"
        )

        sys.exit(1)

    context_file = sys.argv[1]

    try:

        with open(
            context_file,
            "r",
            encoding="utf-8"
        ) as file:

            context = json.load(file)

    except FileNotFoundError:

        print(
            f"ERROR: Context file not found: "
            f"{context_file}"
        )

        sys.exit(1)

    except json.JSONDecodeError as e:

        print(
            f"ERROR: Invalid JSON in context file: "
            f"{e}"
        )

        sys.exit(1)

    try:

        print()
        print(
            "[1/4] Running Qwen RCA analysis..."
        )

        qwen_result = call_qwen(
            context
        )

        print(
            "      Qwen analysis completed."
        )

        print(
            "[2/4] Running Jev independent evaluation..."
        )

        jev_result = call_jev(
            context,
            qwen_result
        )

        print(
            "      Jev evaluation completed."
        )

        print(
            "[3/4] Running deterministic guardrail..."
        )

        guardrail_result = run_guardrail(
            context,
            qwen_result,
            jev_result
        )

        print(
            "      Guardrail evaluation completed."
        )

        print(
            "[4/4] Building human-readable RCA report..."
        )

        report = build_report(
            context,
            qwen_result,
            jev_result,
            guardrail_result
        )

        with open(
            REPORT_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                report,
                file,
                indent=2
            )

        print(
            "      RCA report completed."
        )

        print_report(
            report
        )

        print(
            "\nStructured report saved to:"
        )

        print(
            f"  {REPORT_FILE}"
        )

        print()
        print(
            "NOTE: This pipeline does NOT execute "
            "any remediation action."
        )

    except Exception as e:

        print()
        print("=" * 70)
        print("PIPELINE FAILED")
        print("=" * 70)

        print(
            f"{type(e).__name__}: {e}"
        )

        print("=" * 70)

        sys.exit(1)


if __name__ == "__main__":
    main()

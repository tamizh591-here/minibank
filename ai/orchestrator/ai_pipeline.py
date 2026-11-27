import json
import sys
import urllib.request
import urllib.error


# ============================================================
# Guardrail Import
# ============================================================

GUARDRAIL_PATH = "/projects/minibank/ai/guardrail"

if GUARDRAIL_PATH not in sys.path:
    sys.path.insert(0, GUARDRAIL_PATH)

from guardrail import evaluate


# ============================================================
# Configuration
# ============================================================

RCA_URL = "http://localhost:9100/api/rca"
OLLAMA_URL = "http://localhost:11434/api/chat"

MODEL = "qwen2.5:3b"

REPORT_FILE = (
    "/projects/minibank/ai/orchestrator/"
    "latest-rca-report.json"
)


# ============================================================
# Evaluator JSON Schema
# ============================================================

EVALUATOR_SCHEMA = {
    "type": "object",
    "properties": {
        "rca_support": {
            "type": "object",
            "properties": {
                "choice": {
                    "type": "string",
                    "enum": [
                        "supported",
                        "contradicted",
                        "insufficient_evidence"
                    ]
                },
                "probabilities": {
                    "type": "object",
                    "properties": {
                        "supported": {
                            "type": "number"
                        },
                        "contradicted": {
                            "type": "number"
                        },
                        "insufficient_evidence": {
                            "type": "number"
                        }
                    },
                    "required": [
                        "supported",
                        "contradicted",
                        "insufficient_evidence"
                    ]
                },
                "confidence": {
                    "type": "number"
                }
            },
            "required": [
                "choice",
                "probabilities",
                "confidence"
            ]
        },
        "action_support": {
            "type": "object",
            "properties": {
                "choice": {
                    "type": "string",
                    "enum": [
                        "supported",
                        "not_supported",
                        "needs_review"
                    ]
                },
                "probabilities": {
                    "type": "object",
                    "properties": {
                        "supported": {
                            "type": "number"
                        },
                        "not_supported": {
                            "type": "number"
                        },
                        "needs_review": {
                            "type": "number"
                        }
                    },
                    "required": [
                        "supported",
                        "not_supported",
                        "needs_review"
                    ]
                },
                "confidence": {
                    "type": "number"
                }
            },
            "required": [
                "choice",
                "probabilities",
                "confidence"
            ]
        }
    },
    "required": [
        "rca_support",
        "action_support"
    ]
}


# ============================================================
# Generic HTTP POST
# ============================================================

def post_json(
    url,
    payload,
    headers=None,
    timeout=180
):

    request_headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
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

            body = response.read().decode(
                "utf-8"
            )

            return json.loads(
                body
            )

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
            f"Unable to connect to "
            f"{url}: {e.reason}"
        ) from e


# ============================================================
# Helper
# Convert value to numeric when possible
# ============================================================

def numeric_value(
    value
):

    if isinstance(
        value,
        (int, float)
    ):
        return float(value)

    return None


# ============================================================
# Helper
# Remove nulls from metric arrays
# ============================================================

def clean_numeric_array(
    values
):

    if not isinstance(
        values,
        list
    ):
        return []

    cleaned = []

    for value in values:

        number = numeric_value(
            value
        )

        if number is not None:

            cleaned.append(
                number
            )

    return cleaned


# ============================================================
# Helper
# Summarize a metric array
# ============================================================

def summarize_metric(
    values
):

    cleaned = clean_numeric_array(
        values
    )

    if not cleaned:

        return {
            "samples": 0,
            "minimum": None,
            "maximum": None,
            "average": None,
            "latest": None
        }

    return {
        "samples": len(cleaned),
        "minimum": min(cleaned),
        "maximum": max(cleaned),
        "average": (
            sum(cleaned)
            / len(cleaned)
        ),
        "latest": cleaned[-1]
    }


# ============================================================
# Extract metric arrays recursively
# ============================================================

def find_metric_values(
    data,
    metric_name
):

    if isinstance(
        data,
        dict
    ):

        for key, value in data.items():

            if (
                str(key).lower()
                == metric_name.lower()
            ):

                if isinstance(
                    value,
                    list
                ):
                    return value

            result = find_metric_values(
                value,
                metric_name
            )

            if result is not None:
                return result

    elif isinstance(
        data,
        list
    ):

        for item in data:

            result = find_metric_values(
                item,
                metric_name
            )

            if result is not None:
                return result

    return None


# ============================================================
# Build Compact Evaluator Context
# ============================================================

def build_compact_evidence(
    context,
    qwen_result
):

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


    # --------------------------------------------------------
    # CPU
    # --------------------------------------------------------

    cpu_values = find_metric_values(
        infrastructure,
        "cpu"
    )

    if cpu_values is None:
        cpu_values = []


    # --------------------------------------------------------
    # Memory
    # --------------------------------------------------------

    memory_values = find_metric_values(
        infrastructure,
        "memory"
    )

    if memory_values is None:
        memory_values = []


    # --------------------------------------------------------
    # Keep evidence small for 3B model
    # --------------------------------------------------------

    if not isinstance(
        logs,
        list
    ):
        logs = []


    if not isinstance(
        traces,
        list
    ):
        traces = []


    compact_logs = logs[:5]

    compact_traces = traces[:5]


    # --------------------------------------------------------
    # Compact context
    # --------------------------------------------------------

    compact = {

        "incident": {

            "problem_id":
                incident.get(
                    "problem_id"
                ),

            "problem_name":
                incident.get(
                    "problem_name"
                ),

            "status":
                incident.get(
                    "status"
                ),

            "category":
                incident.get(
                    "category"
                ),

            "description":
                incident.get(
                    "description"
                ),

            "affected_entities":
                incident.get(
                    "affected_entities",
                    []
                )
        },


        "metric_summary": {

            "cpu_percent":
                summarize_metric(
                    cpu_values
                ),

            "memory_percent":
                summarize_metric(
                    memory_values
                )
        },


        "log_summary": {

            "records_found":
                len(logs),

            "sample":
                compact_logs
        },


        "trace_summary": {

            "records_found":
                len(traces),

            "sample":
                compact_traces
        },


        "investigator_proposal": {

            "root_cause":
                qwen_result.get(
                    "root_cause"
                ),

            "recommended_action":
                qwen_result.get(
                    "recommended_action"
                ),

            "reason":
                qwen_result.get(
                    "reason"
                ),

            "confidence":
                qwen_result.get(
                    "confidence"
                )
        }
    }


    return compact


# ============================================================
# STEP 1
# Qwen Investigator
# ============================================================

def call_qwen(
    context
):

    print(
        "      Sending incident context "
        "to RCA service..."
    )

    result = post_json(
        RCA_URL,
        context,
        timeout=180
    )


    if result.get(
        "status"
    ) != "SUCCESS":

        raise RuntimeError(
            f"RCA service failed: {result}"
        )


    if "rca" not in result:

        raise RuntimeError(
            "RCA service response does not "
            "contain 'rca'"
        )


    rca = result[
        "rca"
    ]


    if not isinstance(
        rca,
        dict
    ):

        raise RuntimeError(
            "RCA result must be "
            "a JSON object"
        )


    print()
    print(
        "========== QWEN INVESTIGATOR OUTPUT =========="
    )

    print(
        json.dumps(
            rca,
            indent=2
        )
    )

    print(
        "=============================================="
    )

    print()


    return rca


# ============================================================
# STEP 2
# Local AI Evaluator
# ============================================================

def call_local_evaluator(
    context,
    qwen_result
):

    compact_evidence = (
        build_compact_evidence(
            context,
            qwen_result
        )
    )


    print()
    print(
        "========== COMPACT EVALUATOR INPUT =========="
    )

    print(
        json.dumps(
            compact_evidence,
            indent=2
        )
    )

    print(
        "============================================="
    )

    print()


    system_prompt = """
You are the safety evaluator for the MiniBank AIOps self-healing POC.

Another AI investigator proposed a root cause and remediation action.

Your job is to independently judge whether the RAW incident evidence
supports that root cause and whether it supports the proposed action.

You are NOT the investigator.

You are NOT allowed to execute anything.

Use only the supplied evidence.

IMPORTANT RULES:

1. Do not trust the investigator confidence.

2. Do not repeat the investigator conclusion unless evidence supports it.

3. Do not invent logs, traces, metrics, dependencies or failures.

4. Process unavailable proves that the process became unavailable.
   It does not automatically prove WHY.

5. CPU or memory exhaustion requires strong supporting resource evidence.

6. Low or moderate CPU does not support CPU exhaustion.

7. Moderate memory usage does not support memory exhaustion.

8. A brief CPU spike does not automatically establish resource exhaustion.

9. Historical successful HTTP traces only prove that those requests
   succeeded at those timestamps.

10. Historical health-check traces do not prove current service health.

11. Evaluate RCA and action independently.

12. A restart is not supported merely because it might restore service.

13. If evidence cannot establish the RCA, use insufficient_evidence.

14. If there is not enough evidence to safely validate the action,
    use needs_review.

RCA choice must be exactly one of:

supported
contradicted
insufficient_evidence

Action choice must be exactly one of:

supported
not_supported
needs_review

Return only the JSON required by the provided JSON schema.

Probability values and confidence values must be numbers between 0 and 1.

Do not use strings such as High, Medium or Low for confidence.
"""


    user_prompt = (
        "Evaluate this MiniBank incident.\n\n"
        +
        json.dumps(
            compact_evidence,
            indent=2
        )
    )


    payload = {

        "model": MODEL,

        "messages": [

            {
                "role": "system",
                "content":
                    system_prompt
            },

            {
                "role": "user",
                "content":
                    user_prompt
            }

        ],

        "stream": False,

        # ----------------------------------------------------
        # Structured output schema instead of format=json
        # ----------------------------------------------------

        "format":
            EVALUATOR_SCHEMA,

        "options": {

            "temperature": 0,

            # Keep enough room for the small structured result
            "num_predict": 500
        }
    }


    result = post_json(
        OLLAMA_URL,
        payload,
        timeout=180
    )


    message = result.get(
        "message",
        {}
    )


    content = message.get(
        "content"
    )


    if not content:

        raise RuntimeError(
            "Local evaluator returned "
            "no content"
        )


    # ========================================================
    # Raw evaluator output
    # ========================================================

    print()
    print(
        "========== RAW LOCAL EVALUATOR CONTENT =========="
    )

    print(
        content
    )

    print(
        "=================================================="
    )

    print()


    # ========================================================
    # Parse evaluator output
    # ========================================================

    try:

        evaluation = json.loads(
            content
        )

    except json.JSONDecodeError as e:

        raise RuntimeError(
            "Local evaluator returned "
            "invalid JSON"
        ) from e


    print()
    print(
        "========== PARSED LOCAL EVALUATOR OUTPUT =========="
    )

    print(
        json.dumps(
            evaluation,
            indent=2
        )
    )

    print(
        "===================================================="
    )

    print()


    # ========================================================
    # STRICT validation
    # ========================================================

    validate_evaluator_result(
        evaluation
    )


    return {

        "model":
            MODEL,

        "provider":
            "local_ollama",

        "answers":
            evaluation
    }


# ============================================================
# Evaluator Validation
# ============================================================

def validate_evaluator_result(
    evaluation
):

    if not isinstance(
        evaluation,
        dict
    ):

        raise RuntimeError(
            "Evaluator result must "
            "be a JSON object"
        )


    # --------------------------------------------------------
    # Do not accept {}
    # --------------------------------------------------------

    if not evaluation:

        raise RuntimeError(
            "Evaluator returned "
            "an empty JSON object"
        )


    # --------------------------------------------------------
    # RCA
    # --------------------------------------------------------

    if "rca_support" not in evaluation:

        raise RuntimeError(
            "Evaluator result missing "
            "rca_support"
        )


    # --------------------------------------------------------
    # Action
    # --------------------------------------------------------

    if "action_support" not in evaluation:

        raise RuntimeError(
            "Evaluator result missing "
            "action_support"
        )


    rca = evaluation[
        "rca_support"
    ]

    action = evaluation[
        "action_support"
    ]


    if not isinstance(
        rca,
        dict
    ):

        raise RuntimeError(
            "rca_support must "
            "be an object"
        )


    if not isinstance(
        action,
        dict
    ):

        raise RuntimeError(
            "action_support must "
            "be an object"
        )


    # ========================================================
    # Choices
    # ========================================================

    valid_rca_choices = {
        "supported",
        "contradicted",
        "insufficient_evidence"
    }


    valid_action_choices = {
        "supported",
        "not_supported",
        "needs_review"
    }


    rca_choice = rca.get(
        "choice"
    )


    action_choice = action.get(
        "choice"
    )


    if rca_choice not in valid_rca_choices:

        raise RuntimeError(
            "Invalid RCA choice: "
            f"{rca_choice}"
        )


    if action_choice not in valid_action_choices:

        raise RuntimeError(
            "Invalid action choice: "
            f"{action_choice}"
        )


    # ========================================================
    # Probabilities
    # ========================================================

    validate_probability_object(
        section=rca,
        section_name="rca_support",
        expected_keys={
            "supported",
            "contradicted",
            "insufficient_evidence"
        }
    )


    validate_probability_object(
        section=action,
        section_name="action_support",
        expected_keys={
            "supported",
            "not_supported",
            "needs_review"
        }
    )


    # ========================================================
    # Confidence
    # ========================================================

    validate_confidence(
        rca,
        "rca_support"
    )


    validate_confidence(
        action,
        "action_support"
    )


    print(
        "Evaluator contract validation: PASS"
    )


# ============================================================
# Validate Probability Object
# ============================================================

def validate_probability_object(
    section,
    section_name,
    expected_keys
):

    probabilities = section.get(
        "probabilities"
    )


    # Important:
    # arrays such as [0.3, 0.4, 0.3]
    # are deliberately rejected.

    if not isinstance(
        probabilities,
        dict
    ):

        raise RuntimeError(
            f"{section_name}.probabilities "
            "must be a named JSON object"
        )


    missing = (
        expected_keys
        - set(
            probabilities.keys()
        )
    )


    if missing:

        raise RuntimeError(
            f"{section_name}.probabilities "
            f"missing keys: {sorted(missing)}"
        )


    total = 0.0


    for key in expected_keys:

        value = probabilities[
            key
        ]


        if not isinstance(
            value,
            (int, float)
        ):

            raise RuntimeError(
                f"{section_name}."
                f"probabilities.{key} "
                "must be numeric"
            )


        value = float(
            value
        )


        if value < 0 or value > 1:

            raise RuntimeError(
                f"{section_name}."
                f"probabilities.{key} "
                "must be between 0 and 1"
            )


        total += value


    # Small rounding tolerance

    if total < 0.95 or total > 1.05:

        raise RuntimeError(
            f"{section_name} probabilities "
            "must approximately sum to 1. "
            f"Current total: {total:.3f}"
        )


# ============================================================
# Validate Confidence
# ============================================================

def validate_confidence(
    section,
    section_name
):

    confidence = section.get(
        "confidence"
    )


    if not isinstance(
        confidence,
        (int, float)
    ):

        raise RuntimeError(
            f"{section_name}.confidence "
            "must be numeric"
        )


    confidence = float(
        confidence
    )


    if confidence < 0 or confidence > 1:

        raise RuntimeError(
            f"{section_name}.confidence "
            "must be between 0 and 1"
        )


# ============================================================
# STEP 3
# Deterministic Guardrail
# ============================================================

def run_guardrail(
    context,
    qwen_result,
    evaluator_result
):

    target_service = (
        context
        .get(
            "analysis_request",
            {}
        )
        .get(
            "target_service"
        )
    )


    if not target_service:

        raise RuntimeError(
            "analysis_request."
            "target_service is missing"
        )


    answers = evaluator_result.get(
        "answers",
        {}
    )


    print()
    print(
        "Running deterministic guardrail "
        f"for service: {target_service}"
    )


    result = evaluate(
        qwen_result,
        answers,
        target_service
    )


    if not isinstance(
        result,
        dict
    ):

        raise RuntimeError(
            "Guardrail returned "
            "invalid result"
        )


    print()
    print(
        "========== GUARDRAIL OUTPUT =========="
    )

    print(
        json.dumps(
            result,
            indent=2
        )
    )

    print(
        "======================================"
    )

    print()


    return result


# ============================================================
# STEP 4
# Build Report
# ============================================================

def build_report(
    context,
    qwen_result,
    evaluator_result,
    guardrail_result
):

    incident = context.get(
        "incident",
        {}
    )


    answers = evaluator_result.get(
        "answers",
        {}
    )


    report = {

        "report_version":
            "1.3",

        "title":
            "MiniBank AI Incident Analysis",


        "incident": {

            "problem_id":
                incident.get(
                    "problem_id"
                ),

            "problem_name":
                incident.get(
                    "problem_name"
                ),

            "status":
                incident.get(
                    "status"
                ),

            "category":
                incident.get(
                    "category"
                ),

            "description":
                incident.get(
                    "description"
                ),

            "start_time":
                incident.get(
                    "start_time"
                ),

            "end_time":
                incident.get(
                    "end_time"
                ),

            "affected_entities":
                incident.get(
                    "affected_entities",
                    []
                )
        },


        "qwen_analysis": {

            "role":
                "investigator",

            "model":
                MODEL,

            "root_cause":
                qwen_result.get(
                    "root_cause"
                ),

            "evidence":
                qwen_result.get(
                    "evidence",
                    []
                ),

            "recommended_action":
                qwen_result.get(
                    "recommended_action"
                ),

            "reason":
                qwen_result.get(
                    "reason"
                ),

            "confidence":
                qwen_result.get(
                    "confidence"
                )
        },


        "evaluator_validation": {

            "provider":
                evaluator_result.get(
                    "provider"
                ),

            "model":
                evaluator_result.get(
                    "model"
                ),

            "rca":
                answers.get(
                    "rca_support",
                    {}
                ),

            "action":
                answers.get(
                    "action_support",
                    {}
                )
        },


        "final_decision": {

            "decision":
                guardrail_result.get(
                    "decision"
                ),

            "approved_action":
                guardrail_result.get(
                    "approved_action"
                ),

            "reason":
                guardrail_result.get(
                    "reason"
                ),

            "validation":
                guardrail_result.get(
                    "validation",
                    {}
                )
        },


        "architecture_note": (
            "Qwen2.5:3B is used for the investigator "
            "and evaluator in separate inference passes. "
            "The evaluator receives condensed evidence. "
            "The deterministic Python guardrail remains "
            "the final execution authority."
        )
    }


    return report


# ============================================================
# Save Report
# ============================================================

def save_report(
    report
):

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


# ============================================================
# Format Percentage
# ============================================================

def format_percent(
    value
):

    if not isinstance(
        value,
        (int, float)
    ):

        return str(
            value
        )

    return (
        f"{float(value) * 100:.1f}%"
    )


# ============================================================
# Human-readable Report
# ============================================================

def print_report(
    report
):

    incident = report[
        "incident"
    ]

    qwen = report[
        "qwen_analysis"
    ]

    evaluator = report[
        "evaluator_validation"
    ]

    decision = report[
        "final_decision"
    ]


    print()
    print("=" * 70)
    print(
        "MINIBANK AI INCIDENT ANALYSIS"
    )
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


    print()
    print("QWEN INVESTIGATOR")
    print("-" * 70)


    print(
        f"Root Cause       : "
        f"{qwen.get('root_cause')}"
    )


    print(
        f"Action           : "
        f"{qwen.get('recommended_action')}"
    )


    print(
        f"Confidence       : "
        f"{qwen.get('confidence')}"
    )


    print()
    print("LOCAL AI EVALUATOR")
    print("-" * 70)


    rca = evaluator.get(
        "rca",
        {}
    )


    action = evaluator.get(
        "action",
        {}
    )


    print(
        f"RCA Choice       : "
        f"{rca.get('choice')}"
    )


    print(
        f"RCA Confidence   : "
        f"{format_percent(rca.get('confidence'))}"
    )


    print(
        f"Action Choice    : "
        f"{action.get('choice')}"
    )


    print(
        f"Action Confidence: "
        f"{format_percent(action.get('confidence'))}"
    )


    print()
    print("FINAL GUARDRAIL")
    print("-" * 70)


    print(
        f"Decision         : "
        f"{decision.get('decision')}"
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
# Pipeline
# ============================================================

def run_pipeline(
    context
):

    print()
    print(
        "[1/4] Qwen RCA investigation..."
    )


    qwen_result = call_qwen(
        context
    )


    print()
    print(
        "[2/4] Local AI evaluation..."
    )


    evaluator_result = (
        call_local_evaluator(
            context,
            qwen_result
        )
    )


    print()
    print(
        "[3/4] Deterministic guardrail..."
    )


    guardrail_result = (
        run_guardrail(
            context,
            qwen_result,
            evaluator_result
        )
    )


    print()
    print(
        "[4/4] Building report..."
    )


    report = build_report(
        context,
        qwen_result,
        evaluator_result,
        guardrail_result
    )


    save_report(
        report
    )


    print_report(
        report
    )


    return report


# ============================================================
# CLI
# ============================================================

def main():

    if len(
        sys.argv
    ) != 2:

        print(
            "Usage:"
        )

        print(
            "python3 ai_pipeline.py "
            "<incident-context.json>"
        )

        sys.exit(1)


    context_file = sys.argv[
        1
    ]


    try:

        with open(
            context_file,
            "r",
            encoding="utf-8"
        ) as file:

            context = json.load(
                file
            )


        run_pipeline(
            context
        )


    except Exception as e:

        print()
        print("=" * 70)

        print(
            "PIPELINE FAILED"
        )

        print("=" * 70)


        print(
            f"{type(e).__name__}: {e}"
        )


        print()
        print(
            "SAFETY STATE:"
        )

        print(
            "No remediation was executed."
        )


        print("=" * 70)

        sys.exit(1)


if __name__ == "__main__":
    main()

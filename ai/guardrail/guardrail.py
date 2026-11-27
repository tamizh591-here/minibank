import urllib.request
import urllib.error
import json
import sys
from pathlib import Path


KHUB_PATH = Path(
    "/projects/minibank/ai/khub/minibank-knowledge.json"
)

MIN_RCA_SUPPORT = 0.80
MIN_ACTION_SUPPORT = 0.80

HEALTH_ENDPOINTS = {
    "customer": "http://localhost/customer-service/actuator/health",
    "account": "http://localhost/account-service/actuator/health",
    "transaction": "http://localhost/transaction-service/actuator/health",
    "notification": "http://localhost/notification-service/actuator/health"
}

def is_service_healthy(service_name):

    health_url = HEALTH_ENDPOINTS.get(service_name)

    if not health_url:
        return None

    try:
        with urllib.request.urlopen(
            health_url,
            timeout=5
        ) as response:

            data = json.loads(
                response.read().decode("utf-8")
            )

            return data.get("status") == "UP"

    except (
        urllib.error.URLError,
        TimeoutError,
        json.JSONDecodeError
    ):
        return False


def load_khub():
    with KHUB_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def evaluate(qwen, jev, target_service):

    khub = load_khub()

    service = khub["services"].get(target_service)

    if not service:
        return {
            "decision": "ESCALATE",
            "approved_action": None,
            "reason": "Target service is not defined in K-Hub."
        }

    action = qwen.get("recommended_action")

    allowed_actions = service.get("allowed_actions", [])

    # 1. Action must exist in our allow-list
    if action not in allowed_actions:
        return {
            "decision": "REJECT",
            "approved_action": None,
            "reason": f"Action {action} is not allow-listed."
        }

    rca_eval = jev.get("rca_support", {})
    action_eval = jev.get("action_support", {})

    rca_choice = rca_eval.get("choice")
    action_choice = action_eval.get("choice")

    rca_supported_probability = (
        rca_eval
        .get("probabilities", {})
        .get("supported", 0.0)
    )

    action_supported_probability = (
        action_eval
        .get("probabilities", {})
        .get("supported", 0.0)
    )

    # 2. Jev must explicitly support the RCA
    if rca_choice != "supported":
        return {
            "decision": "ESCALATE",
            "approved_action": None,
            "reason": (
                f"RCA was not validated by Jev. "
                f"Evaluation: {rca_choice}"
            )
        }

    # 3. RCA support must meet threshold
    if rca_supported_probability < MIN_RCA_SUPPORT:
        return {
            "decision": "ESCALATE",
            "approved_action": None,
            "reason": (
                "RCA support probability is below "
                f"{MIN_RCA_SUPPORT:.0%}."
            )
        }

    # 4. Jev must explicitly support the action
    if action_choice != "supported":
        return {
            "decision": "ESCALATE",
            "approved_action": None,
            "reason": (
                f"Action was not validated by Jev. "
                f"Evaluation: {action_choice}"
            )
        }

    # 5. Action support must meet threshold
    if action_supported_probability < MIN_ACTION_SUPPORT:
        return {
            "decision": "ESCALATE",
            "approved_action": None,
            "reason": (
                "Action support probability is below "
                f"{MIN_ACTION_SUPPORT:.0%}."
            )
        }

     # 6. Verify current service health before remediation
    service_healthy = is_service_healthy(target_service)

    if service_healthy is None:
        return {
            "decision": "ESCALATE",
            "approved_action": None,
            "reason": "No health endpoint is configured for target service."
        }

    if service_healthy:
        return {
            "decision": "NO_ACTION",
            "approved_action": None,
            "reason": (
                f"{target_service} is currently healthy. "
                "Remediation is no longer required."
            )
        }   

    return {
        "decision": "APPROVE",
        "approved_action": action,
        "reason": "RCA and remediation action passed guardrail policy.",
        "validation": {
            "rca_supported_probability": rca_supported_probability,
            "action_supported_probability": action_supported_probability
        }
    }


if __name__ == "__main__":

    test_qwen = {
        "root_cause": "host resource exhaustion",
        "recommended_action": "RESTART_CUSTOMER_SERVICE",
        "confidence": 0.80
    }

    test_jev = {
        "rca_support": {
            "choice": "contradicted",
            "confidence": 0.76,
            "probabilities": {
                "contradicted": 0.84,
                "supported": 0.0,
                "insufficient_evidence": 0.16
            }
        },

        "action_support": {
            "choice": "needs_review",
            "confidence": 0.43,
            "probabilities": {
                "not_supported": 0.37,
                "needs_review": 0.63,
                "supported": 0.0
            }
        }
    }

    result = evaluate(
        test_qwen,
        test_jev,
        "customer"
    )

    print(json.dumps(result, indent=2))

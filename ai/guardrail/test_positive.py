import json

from guardrail import evaluate


qwen_result = {
    "root_cause": "Customer service process is unavailable",
    "evidence": [
        "Dynatrace reports the Customer process as unavailable",
        "Host resources are within normal range",
        "No dependency failure has been identified"
    ],
    "recommended_action": "RESTART_CUSTOMER_SERVICE",
    "reason": (
        "The Customer process is unavailable and the supplied "
        "evidence does not indicate a dependency or host failure."
    ),
    "confidence": 0.92
}


jev_result = {

    "rca_support": {
        "choice": "supported",
        "confidence": 0.91,
        "probabilities": {
            "supported": 0.94,
            "contradicted": 0.01,
            "insufficient_evidence": 0.05
        }
    },

    "action_support": {
        "choice": "supported",
        "confidence": 0.90,
        "probabilities": {
            "supported": 0.93,
            "not_supported": 0.02,
            "needs_review": 0.05
        }
    }
}


result = evaluate(
    qwen_result,
    jev_result,
    "customer"
)

print(json.dumps(result, indent=2))

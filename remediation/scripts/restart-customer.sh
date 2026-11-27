#!/bin/bash

set -u

CUSTOMER_TOMCAT="/projects/dependencies/tomcat/customer"
HEALTH_URL="http://localhost/customer-service/actuator/health"

echo "========================================"
echo "MiniBank Customer Service Remediation"
echo "Started: $(date)"
echo "========================================"

echo "[1/4] Stopping Customer Tomcat..."

"$CUSTOMER_TOMCAT/bin/shutdown.sh" 2>/dev/null || true

sleep 5

echo "[2/4] Checking for remaining Customer Tomcat process..."

PID=$(pgrep -f \
"-Dcatalina.base=$CUSTOMER_TOMCAT" | head -1 || true)

if [ -n "$PID" ]; then
    echo "Customer Tomcat still running with PID $PID"
    echo "Stopping PID $PID..."
    kill "$PID"

    sleep 3
fi

echo "[3/4] Starting Customer Tomcat..."

"$CUSTOMER_TOMCAT/bin/startup.sh"

echo "[4/4] Waiting for Customer Service health..."

for i in {1..12}; do

    sleep 5

    RESPONSE=$(curl -s \
        --max-time 3 \
        "$HEALTH_URL" || true)

    if echo "$RESPONSE" | grep -q '"status":"UP"'; then

        echo "========================================"
        echo "RECOVERY SUCCESSFUL"
        echo "Customer Service is UP"
        echo "Recovered: $(date)"
        echo "========================================"

        exit 0
    fi

    echo "Health check attempt $i/12 failed..."
done

echo "========================================"
echo "RECOVERY FAILED"
echo "Customer Service did not become healthy"
echo "========================================"

exit 1

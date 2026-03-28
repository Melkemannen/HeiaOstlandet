#!/bin/bash
set -e

# Start the FastAPI server and ngrok tunnel for the Tripletex agent.
# Usage: ./run.sh [port]

PORT=${1:-8000}

echo "Starting Tripletex agent on port $PORT..."
uvicorn server:app --host 0.0.0.0 --port $PORT &
SERVER_PID=$!

echo "Starting ngrok tunnel..."
ngrok http $PORT &
NGROK_PID=$!

echo ""
echo "Server PID: $SERVER_PID"
echo "ngrok PID:  $NGROK_PID"
echo ""
echo "Check ngrok dashboard at http://localhost:4040 for your public HTTPS URL."
echo "Press Ctrl+C to stop both."

trap "kill $SERVER_PID $NGROK_PID 2>/dev/null" EXIT
wait

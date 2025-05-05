#!/bin/bash

# Start the OpenFabric server in the background
poetry run python ignite.py &
BACKEND_PID=$!

# Wait for the server to start
echo "Waiting for backend server to start..."
sleep 5
echo "Backend server started with PID: $BACKEND_PID"

# Start the Streamlit app
echo "Starting Streamlit frontend..."
poetry run streamlit run app.py --server.port=8501 --server.address=0.0.0.0 &
FRONTEND_PID=$!
echo "Frontend started with PID: $FRONTEND_PID"

# Handle termination signals
trap "kill $BACKEND_PID $FRONTEND_PID; exit" SIGINT SIGTERM

# Keep the container running
echo "Services started. Press Ctrl+C to stop."
wait

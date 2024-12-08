#!/bin/bash

# Print barner with the name of the project

echo -e '\x1b[34m               #                      m                    "          \x1b[0m'
echo -e '\x1b[36m  m mm  m   m  #mmm    mmm   m mm   mm#mm   mmm    m mm  mmm     mmm  \x1b[0m'
echo -e '\x1b[37m  #"  " #   #  #" "#  #"  #  #"  #    #    "   #   #"  "   #    #" "# \x1b[0m'
echo -e '\x1b[30m  #     #   #  #   #  #""""  #   #    #    m"""#   #       #    #   # \x1b[0m'
echo -e '\x1b[35m  #     "mm"#  ##m#"  "#mm"  #   #    "mm  "mm"#   #     mm#mm  "#m#" \x1b[0m'

# Check if the node name is provided
if [ "$#" -ne 1 ]; then
	echo "Usage: ./start_node.sh <node_name>"
	exit 1
fi

NODE_ID=$1

# Check if the node name is right
if [[ ! "$NODE_ID" =~ ^[a-zA-Z0-9_]+$ ]]; then
	echo "Node name must contain only letters, numbers, and underscores."
	exit 1
fi

REQUEST_QUEUE="${NODE_ID}_requests"
RESPONSE_QUEUE="${NODE_ID}_responses"

# Check for available port (starting from 5000)
PORT=5000
while lsof -i:$PORT > /dev/null; do
	PORT=$((PORT + 1))
done

echo "Starting node $NODE_ID on port $PORT with queues $REQUEST_QUEUE and $RESPONSE_QUEUE..."

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
	python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the Python node script with dynamic parameters
python srcs/node.py --id "$NODE_ID" --request_queue "$REQUEST_QUEUE" --response_queue "$RESPONSE_QUEUE" --port "$PORT"

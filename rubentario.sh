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

echo "Creating database . . ."
./postgresql.sh "${NODE_ID}"

# Check for available port (starting from 5000)
PORT=5000
while lsof -i:$PORT > /dev/null; do
	PORT=$((PORT + 1))
done

echo "Starting node $NODE_ID on port $PORT with queues $REQUESTS_QUEUE"

echo "Running Rubentario server . . ."
# Run the Python node script with dynamic parameters
python3 srcs/node.py --id "$NODE_ID" --port "$PORT"

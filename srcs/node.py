from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from threading import Lock
import pika
import json
import threading
import argparse

app = Flask(__name__)
app.secret_key = "vc0910$$"

#Predifined users
users = {
    "admin": "vc0910$$",
}

class Node:
    def __init__(self, id, requests_queue):
        self.lock = Lock()
        self.id = id
		# Requests received from other nodes
        self.requests_queue = requests_queue
        try:
            self.publish_connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
			self.consume_connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        except pika.exceptions.AMQPConnectionError as e:
            print(f"Error connecting to RabbitMQ: {e}")
            raise e
    
        # Consume channel for listening to requests from other nodes
        self.consume_channel = self.consume_connection.channel()
        self.consume_channel.queue_declare(queue=self.requests_queue)

        # Publish channel for sending requests and responses to other nodes
        self.publish_channel = self.publish_connection.channel()

        # Local inventory for the node
        self.inventory = {}

        # Notifications for incoming requests
        self.requests = []

        # Start listening in a thread
        self.listening_thread = threading.Thread(target=self.start_listening, daemon=True).start()

    def handle_request(self, ch, method, properties, body):
        """Handle a request received in the request queue."""
        message = json.loads(body)
        origin_node = message.get("origin_node")
        product = message.get("product")
        quantity = message.get("quantity")
        with self.lock:
            self.requests_queue.append({"origin_node": origin_node, "product": product, "quantity": quantity})

    def send_request(self, destination_node, product, quantity):
        """Send a request to another node."""
        message = {"origin_node": self.id, "product": product, "quantity": quantity}
        try:
            self.publish_channel.basic_publish(exchange='', routing_key=destination_node, body=json.dumps(message))
        except pika.exceptions.AMQError as e:
            print(f"Error sending request to {destination_node} ({e})")

    def start_listening(self):
        """Start listening on the requests queue."""
        self.consume_channel.basic_consume(queue=self.requests_queue, on_message_callback=self.handle_request, auto_ack=True)
		self.consume_channel.start_consuming()

    def stop_listening(self):
        """Stop listening safely."""
        self.stop_event.set()
        if self.consume_connection and self.consume_connection.is_open:
            self.consume_connection.close()

# --- Flask Routes ---
@app.route("/")
def index():
    """Home page: Show inventory and requests."""
    if "username" not in session:
        return redirect(url_for("login"))
    return render_template("index.html", node_id = node.id, inventory=node.inventory, requests=node.requests, username=session["username"])

@app.route("/login", methods=["GET", "POST"])
def login():
    """Login page."""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username in users and users[username] == password:
            session["username"] = username
            return redirect(url_for("index"))
        return "Invalid credentials"
    return render_template("login.html", node_id=node.id)

@app.route("/logout")
def logout():
    """Logout the user."""
    session.pop("username", None)
    return redirect(url_for("login"))

@app.route("/buy", methods=["POST"])
def buy_item():
    """Buy an item for the inventory."""
    data = request.json
    seller = data["seller"]
    product = data["product"]
    quantity = int(data["quantity"])

    if product in node.inventory:
        node.inventory[product] += quantity
    else:
        node.inventory[product] = quantity

    return jsonify({"message": f"Added {quantity} units of {product} to inventory from {seller}"}), 200

@app.route("/sell", methods=["POST"])
def sell_item():
    """Sell an item from the inventory."""
    data = request.json
    client = data["client"]
    product = data["product"]
    quantity = int(data["quantity"])

    if product in node.inventory and node.inventory[product] >= quantity:
        node.inventory[product] -= quantity
        return jsonify({"message": f"Sold {quantity} units of {product} to {client}"}), 200
    else:
        return jsonify({"error": f"Not enough stock for {product}"}), 400

@app.route("/inventory", methods=["GET"])
def inventory():
    """Show the current inventory in the warehouse."""
    # Mostrar el inventario en formato JSON
    return jsonify(node.inventory), 200

@app.route("/requests", methods=["GET"])
def requests():
    """Show the current requests queue in the warehouse"""
    return jsonify(node.requests), 200

@app.route("/send_request", methods=["POST"])
def send_request():
    """Send a request to another node."""
    try:
        data = request.json
        destination_node = data["destination_node"] + "_requests"
        product = data["product"]
        quantity = int(data["quantity"])
        print(f"Sending request to {destination_node} for {product} ({quantity} units)")
        node.send_request(destination_node=destination_node, product=product, quantity=quantity)
        return jsonify({"message": f"Request for {product} sent to {destination_node} ({quantity} units)"}), 200
    except KeyError as e:
        return jsonify({"error": f"Missing key in request data ({e})"}), 400
    except ValueError as e:
        return jsonify({"error": f"Invalid quantity ({e})"}), 400
    except Exception as e:
        return jsonify({"error": f"Internal unexpected server error ({str(e)})"}), 500

@app.route("/stop", methods=["POST"])
def stop():
    """Stop the node."""
    node.stop_listening()
    return jsonify({"message": "Node stopped"}), 200

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--id', required=True, help='Node ID')
    parser.add_argument('--request_queue', required=True, help='Request Queue')
    parser.add_argument('--response_queue', required=True, help='Response Queue')
    parser.add_argument('--port', required=True, help='Port for the node')
    args = parser.parse_args()
    node = Node(id=args.id, request_queue=args.request_queue, response_queue=args.response_queue)
    app.run(debug=True, host="0.0.0.0", port=args.port)

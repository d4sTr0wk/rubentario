from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from threading import Lock
import pika
import json
import threading
import argparse
import signal
import sys

app = Flask(__name__)
app.secret_key = "vc0910$$"

#Predifined users
users = {
	"admin": "vc0910$$",
}

class Node:
	def __init__(node, id, requests_queue):
		node.lock = Lock()
		node.id = id
		# Requests received from other nodes
		node.requests_queue = requests_queue
		try:
			node.publish_connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
			node.consume_connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
		except pika.exceptions.AMQPConnectionError as e:
			print(f"Error connecting to RabbitMQ: {e}")
			raise e
	
		# Consume channel for listening to requests from other nodes
		node.consume_channel = node.consume_connection.channel()
		node.consume_channel.queue_declare(queue=node.requests_queue)

		# Publish channel for sending requests and responses to other nodes
		node.publish_channel = node.publish_connection.channel()

		# Local inventory for the node
		node.inventory = {}

		# Notifications for incoming requests
		node.requests = []

def handleRequest(ch, method, properties, body):
	"""Handle a request received in the request queue."""
	message = json.loads(body)
	requester_node = message.get("requester_node")
	product = message.get("product")
	quantity = message.get("quantity")
	with node.lock: 
		node.requests.append({"requester_node": requester_node, "product": product, "quantity": quantity}) # Update requests
		print(f"Updated requests in node{id(node)}: {node.requests}") # Check requests update

def sendRequest(destination_node, product, quantity):
	"""Send a request to another node."""
	message = {"requester_node": node.id, "product": product, "quantity": quantity}
	try:
		node.publish_channel.basic_publish(exchange='', routing_key=destination_node, body=json.dumps(message))
	except pika.exceptions.AMQError as e:
		print(f"Error sending request to {destination_node} ({e})")
def startListening():
	"""Start listening on the requests queue."""
	node.consume_channel.basic_consume(queue=node.requests_queue, on_message_callback=handleRequest, auto_ack=True)
	node.consume_channel.start_consuming()

def stopListening():
	"""Stop listening safely."""
	if node.consume_connection and node.consume_connection.is_open:
		node.consume_connection.close()
	if node.publish_connection and node.publish_connection.is_open:
		node.publish_connection.close()
	sys.exit(0)

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

@app.route("/show_inventory", methods=["GET"])
def show_inventory():
	"""Show the current inventory in the warehouse."""
	# Mostrar el inventario en formato JSON
	with node.lock:
		return jsonify(node.inventory), 200

@app.route("/show_requests", methods=["GET"])
def show_requests():
	"""Show the current requests queue in the warehouse"""
	with node.lock:
		print(f"Current requests in node{id(node)}: {node.requests}")
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
		sendRequest(destination_node=destination_node, product=product, quantity=quantity)
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
	stopListening()
	return jsonify({"message": "Node stopped"}), 200

def signalHandler(sig, frame):
	print("Bye bye!")
	stopListening()

# Assign singal SIGNIT (Ctrl + ^C) to the function
signal.signal(signal.SIGINT, signalHandler)

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument('--id', required=True, help='Node ID')
	parser.add_argument('--requests_queue', required=True, help='Requests Queue')
	parser.add_argument('--port', required=True, help='Port for the node')
	args = parser.parse_args()

	# Create the node object
	node = Node(id=args.id, requests_queue=args.requests_queue) 
	print(f"Node initialized with ID: {id(node)}, requests queue ID: {id(node.requests)}")

	# Start listening in a thread
	listening_thread = threading.Thread(target=startListening, daemon=True).start()

	app.run(debug=True, host="0.0.0.0", port=args.port)

from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from threading import Lock
import pika
import json
import threading
import argparse
import signal
import sys
from pika.spec import methods
import requests
import psycopg2
from psycopg2 import errors
from datetime import datetime


# Database connection
db_conn = psycopg2.connect(
    dbname = "warehouse",
    user = "rubentario",
    password = "rubentario",
    host="localhost",
    port="5432"
)

cursor = db_conn.cursor()
    
app = Flask(__name__)
app.secret_key = "vc0910$$"

#Predifined users
users = {
	"admin": "admin",
}


class Node:
	def __init__(self, id, requests_queue, url, port):
		self.lock = Lock()
		self.id = id
		self.url = url
		self.port = port
		# Requests received from other selfs
		self.requests_queue = requests_queue
		try:
			self.publish_connection = pika.BlockingConnection(pika.ConnectionParameters(self.url))
			self.consume_connection = pika.BlockingConnection(pika.ConnectionParameters(self.url))
		except pika.exceptions.AMQPConnectionError as e:
			print(f"Error connecting to RabbitMQ: {e}")
			raise e

		# Consume channel for listening to requests from other selfs
		self.consume_channel = self.consume_connection.channel()
		self.consume_channel.queue_declare(queue=self.requests_queue, durable=True)

		# Publish channel for sending requests and responses to other selfs
		self.publish_channel = self.publish_connection.channel()

		# Notifications for incoming requests
		cursor.execute('''
			CREATE TABLE IF NOT EXISTS requests (
				requester_node VARCHAR(255) NOT NULL,
				product_id VARCHAR(50) NOT NULL,
				stock INTEGER NOT NULL
			);
		''')
		self.requests_cache = []
		cursor.execute("SELECT * FROM requests;")
		if cursor.rowcount > 0:
			rows = cursor.fetchall()
			self.requests_cache = [
				{"requester_node": str(r[0]), "product_id": str(r[1]), "stock": r[2]} for r in rows
			]

		# PRODUCTS
		cursor.execute('''
			CREATE TABLE IF NOT EXISTS products (
				id VARCHAR(50) PRIMARY KEY,
				name VARCHAR(150) NOT NULL,
				description TEXT,
				unit_price FLOAT,
				weight FLOAT,
				expiration_date DATE
			);
		''')
		self.products_cache = [{}]
		cursor.execute("SELECT * FROM products;")
		if cursor.rowcount > 0:
			rows = cursor.fetchall()
			self.products_cache = [
					{"id": str(r[0]), "name": str(r[1]), "description": str(r[2]), "unit_price": r[3], "weight": r[4], "expiration_date": str(r[5])} for r in rows
			]

		# INVENTORY
		cursor.execute('''
			CREATE TABLE IF NOT EXISTS inventory (
				product_id VARCHAR (50) PRIMARY KEY,
				stock INTEGER NOT NULL,
				CONSTRAINT fk_product_id FOREIGN KEY (product_id) REFERENCES products(id)
			);
		''')
		self.inventory_cache = {}
		cursor.execute("SELECT * FROM inventory;")
		if cursor.rowcount > 0:
			rows = cursor.fetchall()
			self.inventory_cache.update({str(row[0]): row[1] for row in rows})

		# TRANSACTIONS
		cursor.execute('''
			CREATE TABLE IF NOT EXISTS transactions (
				sender VARCHAR(100) NOT NULL,
				receiver VARCHAR(100) NOT NULL,
				product_id VARCHAR(50) NOT NULL,
				stock INTEGER NOT NULL,
				date TIMESTAMP NOT NULL
			);
		''');
		self.transactions_cache = [{}]
		cursor.execute("SELECT * FROM transactions;")
		if cursor.rowcount > 0:
			transactions = cursor.fetchall()
			self.transactions_cache = [
				{"sender": str(t[0]), "receiver": str(t[1]), "product_id": str(t[2]), "stock": t[3], "date": str(t[4])} for t in transactions
			]

		db_conn.commit()


	def handle_request(self, ch, method, properties, body):
		"""Handle a request received in the request queue and send data to main server thread."""
		# Send data to main server
		try:
			headers = {'Content-Type': 'application/json'}
			response = requests.post(f"http://{self.url}:{self.port}/new_request", headers=headers, data=body)
			if response.status_code == 200:
				print("Message sended to server")
			else:
				print(f"Error sending the message: {response.status_code}")
		except Exception as e:
			print(f"Error: {e}")


	def send_request(self, destination_node, product_id, stock):
		try:
			# Reconnect with RabbitMQ
			if not self.publish_connection or self.publish_connection.is_closed:
				print("Closed connection. Trying to open it . . .")
				self.publish_connection = pika.BlockingConnection(pika.ConnectionParameters(self.url))
			if not self.publish_channel or self.publish_channel.is_closed:
				print("Closed channel. Trying create new one . . .")
				self.publish_channel = self.publish_connection.channel()

			message = {"requester_node": node.id, "product_id": product_id, "stock": stock}
			self.publish_channel.basic_publish(exchange='', routing_key=destination_node, body=json.dumps(message)) 

		except pika.exceptions.AMQPChannelError as e:
			print(f"Error in publish_channel: {e}")
		except pika.exceptions.AMQPConnectionError as e:
			print(f"Error in publish_connection: {e}")
		except Exception as e:
			print(f"Error sending request to {destination_node}: ({e})")


	def start_listening(self):
		# Start listening on the requests queue
		try:
			self.consume_channel.basic_consume(queue=self.requests_queue, on_message_callback=self.handle_request, auto_ack=True)
			self.consume_channel.start_consuming()
		except Exception as e:
			print(f"Error with consuming thread: {e}")
		finally:
			print("Consuming thread terminated")


	def stop_listening(self):
		# Stop listening safely
		try:
			if self.consume_channel and not self.consume_channel.is_closed:
				self.consume_channel.close()
			if self.consume_connection and not self.consume_connection.is_closed:
				self.consume_connection.close()
		except Exception as e:
			print(f"Error closing RabbitMQ connections: {e}")


# --- Flask Routes ---
@app.route("/")
def index():
	# Home page: Show inventory and requests
	if "username" not in session:
		return redirect(url_for("login"))

	return render_template("index.html", node_id = node.id, username=session["username"])


@app.route("/login", methods=["GET", "POST"])
def login():
	# Login page
	if request.method == "POST":
		username = request.form["username"]
		password = request.form["password"]
		if username in users and users[username] == password:
			session["username"] = username
			return redirect(url_for('index'))
		return render_template('login.html', error='Invalid credentials')

	return render_template('login.html', node_id=node.id)


"""Logout option"""
@app.route("/logout")
def logout():
	# Logout the user
	session.pop("username", None)
	return redirect(url_for("login"))


"""Receive new request from listening thread and update requests list"""
@app.route("/new_request", methods=["POST"])
def new_request():
	data = request.json
	if data is None:
		return jsonify({"error": "Invalid JSON or no JSON provided"}), 400

	# JSON data exctraction
	requester_node = data["requester_node"]
	product_id = data["product_id"]
	stock = data["stock"]

	# Validate all fields
	if not all([requester_node, product_id, stock]):
		return jsonify({"error": "Missing required fields"}), 400

	with node.lock:
		node.requests_cache.append({
			'requester_node': requester_node,
			'product_id': product_id,
			'stock': stock
		})
		print(f"New request added to node{id(node)} request list {id(node.requests_cache)}: Requester: {requester_node}, Product: {product_id}, Quantity; {stock}")

	return jsonify({"message": "Request added successfully"}), 200


@app.route("/buy", methods=["POST"])
def buy_item():
	# Buy an item for the inventory
	data = request.json
	if data is None:
		return jsonify({"error": "Invalid JSON or no JSON provided"}), 400

	seller = data["seller"]
	product_id = data["product_id"]
	stock = int(data["stock"])

	# Validate all fields
	if not all ([seller, product_id, stock]):
		return jsonify({"error": "Missing required fields"}), 400

	try:
		cursor.execute("SELECT * FROM products WHERE id = %s;", (product_id,))
		if cursor.rowcount == 0:
			return jsonify({"error": f"No product found with id {product_id}"}), 404

		cursor.execute("SELECT * FROM inventory WHERE product_id = %s;", (product_id,))
		if cursor.rowcount == 0:
			cursor.execute("INSERT INTO inventory VALUES (%s, %s);", (product_id, stock))
		else:
			cursor.execute("UPDATE inventory SET stock = stock + %s WHERE product_id = %s;", (stock, product_id))

		cursor.execute("INSERT INTO transactions VALUES (%s, %s, %s, %s, NOW())", (seller, node.id, product_id, stock))

		db_conn.commit()

		with node.lock:
			cursor.execute("SELECT * FROM transactions ORDER BY date DESC LIMIT 1;")
			row = cursor.fetchone()
			if row is not None:
				node.transactions_cache.append(
				{"sender": str(row[0]), "receiver": str(row[1]), "product_id": str(row[2]), "stock": row[3], "date":str(row[4])}
				)

			if str(product_id) in node.inventory_cache:
				node.inventory_cache[str(product_id)] += stock
			else:
				cursor.execute("SELECT stock FROM inventory WHERE product_id = %s;", (product_id,))
				result = cursor.fetchone()
				if result:
					node.inventory_cache[str(product_id)] = result[0]

		return jsonify({"message": f"Added {stock} units of {product_id} to inventory from {seller}"}), 200
	except Exception as e:
		db_conn.rollback()
		return jsonify({"error": f"Intern unexpected server error buying: {e}"}), 500


@app.route("/sell", methods=["POST"])
def sell_item():
	# Sell an item from the inventory
	data = request.json
	if data is None:
		return jsonify({"error": "Invaild JSON or no JSON provided"}), 400

	client = data["client"]
	product_id = data["product_id"]
	stock = int(data["stock"])

	# Validate all fields
	if not all ([client, product_id, stock]):
		return jsonify({"error": "Missing required fields"}), 400

	try:
		cursor.execute("SELECT * FROM products WHERE id = %s;", (product_id,))
		if cursor.rowcount == 0:
			return jsonify({"error": f"No product found with id {product_id}"}), 404

		cursor.execute("SELECT stock FROM inventory WHERE product_id = %s;", (product_id,))
		result = cursor.fetchone()
		if result:
			product_stock = result[0]
			if stock > product_stock:
				db_conn.rollback()
				return jsonify({"error": f"Not enough stock for {product_id}"}), 400
			elif stock == product_stock:
				cursor.execute("DELETE FROM inventory WHERE product_id = %s;", (product_id,))
			else:
				cursor.execute("UPDATE inventory SET stock = stock - %s WHERE product_id = %s;", (stock, product_id))

			cursor.execute("INSERT INTO transactions VALUES (%s, %s, %s, %s, NOW())", (node.id, client, product_id, stock))
		
			db_conn.commit()

			with node.lock:
				cursor.execute("SELECT * FROM transactions ORDER BY date DESC LIMIT 1;")
				row = cursor.fetchone()
				if row is not None:
					node.transactions_cache.append(
					{"sender": str(row[0]), "receiver": str(row[1]), "product_id": str(row[2]), "stock": row[3], "date":str(row[4])}
					)

				if str(product_id) in node.inventory_cache:
					node.inventory_cache[str(product_id)] -= stock
					if node.inventory_cache[str(product_id)] <= 0:
						del node.inventory_cache[str(product_id)]
				else:
					pass

			return jsonify({"message": f"Sold {stock} units of {product_id} to inventory to {client}"}), 200
		else:
			db_conn.rollback()
			return jsonify({"error": f"Product {product_id} not found in inventory table"}), 404

	except Exception as e:
		db_conn.rollback()
		return jsonify({"error": f"Intern unexpected server error selling: {e}"}), 500


@app.route("/api/inventory", methods=["GET"])
def get_inventory():
	print(f"Inventory: { node.inventory_cache }")
	return jsonify(node.inventory_cache), 200


@app.route("/api/products", methods=["GET"])
def get_products():
	print(f"Products: { node.products_cache }")
	return jsonify(node.products_cache), 200

@app.route("/api/requests", methods=["GET"])
def get_requests():
	with node.lock:
		print(f"Current requests in node{id(node)}: {node.requests_cache}")
		return jsonify(node.requests_cache), 200


@app.route("/api/transactions", methods=["GET"])
def get_transactions():
	print(f"Transactions: { node.transactions_cache }")
	return jsonify(node.transactions_cache), 200


@app.route("/send_request", methods=["POST"])
def send_request():
	# Send a request to another node
	try:
		data = request.json
		if data is None:
			return jsonify({"error": "Invalid JSON or no JSON provided"}), 400

		destination_node = data["destination_node"] + "_requests"
		product = data["product"]
		stock = int(data["stock"])

		if not all ([destination_node, product, stock]):
			return jsonify({"error": "Missing required fields"}), 400

		print(f"Sending request to {destination_node} for {product} ({stock} units)")
		node.send_request(destination_node=destination_node, product_id=product, stock=stock)
		return jsonify({"message": f"Request for {product} sent to {destination_node} ({stock} units)"}), 200
	except KeyError as e:
		return jsonify({"error": f"Missing key in request data ({e})"}), 400
	except ValueError as e:
		return jsonify({"error": f"Invalid stock ({e})"}), 400
	except Exception as e:
		return jsonify({"error": f"Internal unexpected server error ({str(e)})"}), 500


@app.route("/add_product", methods=["POST"])
def add_product():
	data = request.json
	if data is None:
		return jsonify({"error": "Invalid JSON or no JSON provided"}), 400

	id = data["id"]
	name = data["name"]
	description = data["description"]
	unit_price = float(data["unit_price"])
	weight = float(data["weight"])
	expiration_date = datetime.strptime(data["expiration_date"], '%Y-%m-%d')

	if not all([id, name, description, unit_price, weight, expiration_date]):
		return jsonify({"error": "Missing required fields"}), 400

	try:
		cursor.execute("INSERT INTO products (id, name, description, unit_price, weight, expiration_date) VALUES (%s, %s, %s, %s, %s, %s);", (id, name, description, unit_price, weight, expiration_date))
		db_conn.commit()

		with node.lock:
			node.products_cache.append({'id': id, 'name': name, 'description': description, 'unit_price': unit_price, 'weight': weight, 'expiration_date': str(expiration_date)})

		return jsonify({"message": f"New product ({name}) added"}), 200
	except errors.UniqueViolation:
		db_conn.rollback()
		return jsonify({"error": f"ID {id} product already exists!"}), 409
	except Exception as e:
		db_conn.rollback()
		return jsonify({"error": f"Intern unexpected server error adding: {e}"}), 500

@app.route("/delete_product", methods=["POST"])
def delete_product():
	data = request.json
	if data is None:
		return jsonify({"error": "Invalid JSON or no JSON provided"}), 400

	id = data["id"]
	if not id:
		return jsonify({"error": "Missing required field"}), 400

	try:
		cursor.execute("DELETE FROM inventory WHERE product_id = %s;", (id,))
		cursor.execute("DELETE FROM products WHERE id = %s;", (id,))
		db_conn.commit()

		with node.lock:
			node.inventory_cache.pop(id)
			for i, item in enumerate(node.products_cache):
				if item.get("id") == id:
					node.products_cache.pop(i)
					break

		if cursor.rowcount == 0:
			return jsonify({"error": f"No product found with id {id}"}), 404

		return jsonify({"message": f"Product {id} deleted from products table and inventory table"}), 200
	except Exception as e:
		db_conn.rollback()
		return jsonify({"error": f"Intern unexpected server error deleting: {e}"}), 500

@app.route("/stop", methods=["POST"])
def stop():
	# Stop the node
	try:
		node.stop_listening()
		if listening_thread and listening_thread.is_alive():
			listening_thread.join()
		cursor.close()
		db_conn.close()
	except Exception as e:
		print(f"Error closing features: {e}")
	finally:
		print("Bye bye!")
	return jsonify({"message": "Node stopped"}), 200

def signalHandler(sig, _):
	print("Bye bye!")
	try:
		node.stop_listening()
		if listening_thread and listening_thread.is_alive():
			listening_thread.join()
	except Exception as e:
		print(f"Error closing features: {e}")
	finally:
		cursor.close()
		db_conn.close()
		sys.exit(0)

# Assign singal SIGNIT (Ctrl + ^C) to the function
signal.signal(signal.SIGINT, signalHandler)
signal.signal(signal.SIGTERM, signalHandler)

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument('--id', required=True, help='Node ID')
	parser.add_argument('--requests_queue', required=True, help='Requests Queue')
	parser.add_argument('--port', required=True, help='Port for the node')
	args = parser.parse_args()

	# Create the node object
	node = Node(id=args.id, requests_queue=args.requests_queue, url='localhost', port=args.port) 
	print(f"Node initialized with ID: {id(node)}, requests queue ID: {id(node.requests_cache)}, PORT: {node.port}")

	# Start listening in a thread
	listening_thread = threading.Thread(target=node.start_listening, daemon=True).start()

	app.run(debug=True, host="0.0.0.0", port=args.port)#, use_reloader=False)

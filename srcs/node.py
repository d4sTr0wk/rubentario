from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_socketio import SocketIO, emit
from threading import Lock
import pika
import json
import threading
import argparse
import signal
import sys
import requests
import psycopg2
import uuid
from psycopg2 import errors
from datetime import datetime

app = Flask(__name__)
app.secret_key = "vc0910$$"

socketio = SocketIO(app)

#Predifined users
users = {
	"admin": "admin",
}


class Node:
	def __init__(self, id, url, port):
		self.lock = Lock()
		self.id = id
		self.url = url
		self.port = port

		# Database connection
		try:
			self.db_conn = psycopg2.connect(
				dbname = self.id + "_warehouse",
				user = "rubentario",
				password = "rubentario",
				host=self.url,
				port="5432"
			)
			self.cursor = self.db_conn.cursor()
			print("Database connection initialized.")
		except Exception as e:
			print(f"Error connection to the database: {e}")
			sys.exit(1)

		# Requests received from other selfs
		self.requests_queue = self.id + "_requests"
		self.query_queue = self.id + "_queries"
		try:
			self.publish_connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.url, heartbeat=60))
			self.request_connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.url, heartbeat=60))
			self.query_connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.url, heartbeat=60))
		except pika.exceptions.AMQPConnectionError as e:
			print(f"Error connecting to RabbitMQ: {e}")
			raise e

		self.request_channel = self.request_connection.channel()
		self.request_channel.queue_declare(queue=self.requests_queue, durable=True)

		self.query_channel = self.query_connection.channel()
		self.query_channel.queue_declare(queue=self.query_queue, durable=True)

		# Publish channel for sending requests and responses to other selfs
		self.publish_channel = self.publish_connection.channel()

		# My requests
		self.cursor.execute('''
				CREATE TABLE IF NOT EXISTS my_requests (
					uuid VARCHAR(36) NOT NULL,	
					destination_node VARCHAR(255) NOT NULL,
					product_id VARCHAR(50) NOT NULL,
					stock INTEGER NOT NULL
				);
		''')
		self.my_requests_cache = []
		self.cursor.execute("SELECT * FROM my_requests;")
		if self.cursor.rowcount > 0:
			rows = self.cursor.fetchall()
			self.my_requests_cache = [
					{"uuid": str(r[0]), "destination_node": str(r[1]), "product_id": str(r[2]), "stock": r[3]} for r in rows
			]

		# Notifications for incoming requests
		self.cursor.execute('''
			CREATE TABLE IF NOT EXISTS requests (
				uuid VARCHAR(36) NOT NULL,
				requester_node VARCHAR(255) NOT NULL,
				product_id VARCHAR(50) NOT NULL,
				stock INTEGER NOT NULL
			);
		''')
		self.requests_cache = []
		self.cursor.execute("SELECT * FROM requests;")
		if self.cursor.rowcount > 0:
			rows = self.cursor.fetchall()
			self.requests_cache = [
					{"uuid": str(r[0]), "requester_node": str(r[1]), "product_id": str(r[2]), "stock": r[3]} for r in rows
			]

		# PRODUCTS
		self.cursor.execute('''
			CREATE TABLE IF NOT EXISTS products (
				id VARCHAR(50) PRIMARY KEY,
				name VARCHAR(150) NOT NULL,
				description TEXT,
				minimum_stock INTEGER NOT NULL,
				unit_price FLOAT,
				weight FLOAT,
				expiration_date DATE
			);
		''')
		self.products_cache = []
		self.cursor.execute("SELECT * FROM products;")
		if self.cursor.rowcount > 0:
			rows = self.cursor.fetchall()
			self.products_cache = [
					{"id": str(r[0]), "name": str(r[1]), "description": str(r[2]), "minimum_stock": r[3], "unit_price": r[4], "weight": r[5], "expiration_date": str(r[6])} for r in rows
			]

		# INVENTORY
		self.cursor.execute('''
			CREATE TABLE IF NOT EXISTS inventory (
				product_id VARCHAR (50) PRIMARY KEY,
				stock INTEGER NOT NULL,
				CONSTRAINT fk_product_id FOREIGN KEY (product_id) REFERENCES products(id)
			);
		''')
		self.inventory_cache = {}
		self.cursor.execute("SELECT * FROM inventory;")
		if self.cursor.rowcount > 0:
			rows = self.cursor.fetchall()
			self.inventory_cache.update({str(row[0]): row[1] for row in rows})

		# TRANSACTIONS
		self.cursor.execute('''
			CREATE TABLE IF NOT EXISTS transactions (
				sender VARCHAR(100) NOT NULL,
				receiver VARCHAR(100) NOT NULL,
				product_id VARCHAR(50) NOT NULL,
				stock INTEGER NOT NULL,
				date TIMESTAMP NOT NULL
			);
		''');
		self.transactions_cache = []
		self.cursor.execute("SELECT * FROM transactions;")
		if self.cursor.rowcount > 0:
			transactions = self.cursor.fetchall()
			self.transactions_cache = [
				{"sender": str(t[0]), "receiver": str(t[1]), "product_id": str(t[2]), "stock": t[3], "date": str(t[4])} for t in transactions
			]

		self.db_conn.commit()


	def handle_request(self, ch, method, properties, body):
		"""Handle a request received in the request queue and send data to main server thread."""
		# Send data to main server
		try:
			headers = {'Content-Type': 'application/json'}
			if properties.headers['message_type'] == 'request':
				response = requests.post(f"http://{self.url}:{self.port}/new_request", headers=headers, data=body)
			else:
				response = requests.post(f"http://{self.url}:{self.port}/request_response", headers=headers, data=body)
			if response.status_code == 200:
				print("Request added successfully!")
			else:
				print(f"Error adding request to server: {response.status_code}")
		except Exception as e:
			print(f"Error: {e}")

	
	def handle_query(self, ch, method, properties, body):
		"""Handle a query received to return node's inventory"""
		try:
			headers = {'Content-Type': 'application/json'}
			if properties.headers['message_type'] == 'query':
				response = requests.post(f"http://{self.url}:{self.port}/new_query", headers=headers, data=body)
			else:
				response = requests.post(f"http://{self.url}:{self.port}/query_response", headers=headers, data=body)
			if response.status_code == 200:
				print("Message sended to server")
			else:
				print(f"Error sending query to server: {response.status_code}")
		except Exception as e:
			print(f"Error: {e}")

	def send_query(self, destination_node, product_id, stock):
		try:
			# Reconnect with RabbitMQ
			if not self.publish_connection or self.publish_connection.is_closed:
				print("Closed connection. Trying to open it . . .")
				self.publish_connection = pika.BlockingConnection(pika.ConnectionParameters(self.url))
			if not self.publish_channel or self.publish_channel.is_closed:
				print("Closed channel. Trying create new one . . .")
				self.publish_channel = self.publish_connection.channel()

			message = {"queryer_node": node.id, "product_id": product_id, "stock": stock}
			self.publish_channel.basic_publish(exchange='', routing_key=destination_node, body=json.dumps(message), properties=pika.BasicProperties(headers={'message_type': 'query'})) 
		except pika.exceptions.AMQPChannelError as e:
			print(f"Error in publish_channel: {e}")
		except pika.exceptions.AMQPConnectionError as e:
			print(f"Error in publish_connection: {e}")
		except Exception as e:
			print(f"Error sending request to {destination_node}: ({e})")


	def send_request(self, destination_node, product_id, stock):
		try:
			# Reconnect with RabbitMQ
			if not self.publish_connection or self.publish_connection.is_closed:
				print("Closed connection. Trying to open it . . .")
				self.publish_connection = pika.BlockingConnection(pika.ConnectionParameters(self.url))
			if not self.publish_channel or self.publish_channel.is_closed:
				print("Closed channel. Trying create new one . . .")
				self.publish_channel = self.publish_connection.channel()

			message = {"uuid": str(uuid.uuid4()), "requester_node": node.id, "product_id": product_id, "stock": stock}
			self.publish_channel.basic_publish(exchange='', routing_key=destination_node, body=json.dumps(message), properties=pika.BasicProperties(headers={'message_type': 'request'})) 

		except pika.exceptions.AMQPChannelError as e:
			print(f"Error in publish_channel: {e}")
		except pika.exceptions.AMQPConnectionError as e:
			print(f"Error in publish_connection: {e}")
		except Exception as e:
			print(f"Error sending request to {destination_node}: ({e})")


	def start_listening_requests(self):
		# Start listening on the requests queue
		try:
			self.request_channel.basic_consume(queue=self.requests_queue, on_message_callback=self.handle_request, auto_ack=True)
			self.request_channel.start_consuming()
		except Exception as e:
			print(f"Error with requests consuming thread: {e}")
		finally:
			print("Requests consuming thread terminated")

	
	def start_listening_queries(self):
		try:
			self.query_channel.basic_consume(queue=self.query_queue, on_message_callback=self.handle_query, auto_ack=True)
			self.query_channel.start_consuming()
		except Exception as e:
			print(f"Error with queries consuming thread: {e}")
		finally:
			print("Queries consuming thread terminated")


	def stop_listening(self):
		# Stop listening safely
		try:
			if self.request_channel and not self.request_channel.is_closed:
				self.request_channel.close()
			if self.request_connection and not self.request_connection.is_closed:
				self.request_connection.close()
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


@app.route("/query_response",methods=["POST"])
def query_response():
	data = request.json
	if data is None:
		return jsonify({"error": "Invalid JSON or no JSON provided"}), 400

	if not data:
		socketio.emit('query_response', data)
		return jsonify({"error": "Product not on node"}), 400

	product_id = data["product_id"]
	stock = int(data["stock"])
	minimum_stock = int(data["minimum_stock"])

	if not all ([product_id, stock, minimum_stock]):
		return jsonify({"error": "Missing required fields"}), 400

	socketio.emit('query_response', data)

	return jsonify({"message": "Response received!"}), 200

"""Receive new query from listening thread and send data to queryer node"""
@app.route("/new_query", methods=["POST"])
def new_query():
	data = request.json
	if data is None:
		return jsonify({"error": "Invalid JSON or no JSON provided"}), 400

	queryer_node = data["queryer_node"]
	product_id = data["product_id"]
	stock = data["stock"]

	if not all([queryer_node, product_id, stock]):
		return jsonify({"error": "Missing required fields"}), 400

	node.cursor.execute("SELECT product_id, stock, products.minimum_stock FROM inventory JOIN products ON products.id = inventory.product_id WHERE id = %s AND inventory.stock >= %s AND inventory.stock - %s > products.minimum_stock;", (product_id,stock,stock))

	row = node.cursor.fetchone()
	if node.cursor.rowcount == 0 or row is None:
		result = {}
	else:
		result = {
				"product_id": str(row[0]),
				"stock": row[1],
				"minimum_stock": row[2]
		}
	print(result)
	message_json = json.dumps(result)

	node.publish_channel.basic_publish(
			exchange='',
			routing_key=queryer_node + '_queries',
			body=message_json,
			properties=pika.BasicProperties(headers={'message_type': 'response'})
			)
	if not result:
		return jsonify({"error": "Product queried is not registered, consequently query is removed"}), 404

	return jsonify({"message": "Query resolved successfully"}), 200


@app.route("/request_response", methods=["POST"])
def request_response():
	data = request.json
	if data is None:
		return jsonify({"error": "Invalid JSON or no JSON provided"}), 400

	if not data:
		socketio.emit('request_response', data)
		return jsonify({"error": "Product not on node"}), 400

	uuid = data["uuid"]
	destination_node = data["destination_node"]
	product_id = data["product_id"]
	stock = int(data["stock"])

	if not all ([product_id, destination_node, stock]):
		return jsonify({"error": "Missing required fields"}), 400
	
	try:
		node.cursor.execute("INSERT INTO my_requests VALUES(%s, %s, %s, %s);", (uuid, destination_node, product_id, stock))

		node.db_conn.commit()	
	except Exception as e:
		node.db_conn.rollback()
		return jsonify({"error": f"Error inserting in request_response: {e}"}), 400

	with node.lock:
		node.my_requests_cache.append({
			'uuid': uuid,
			'destination_node': destination_node,
			'product_id': product_id,
			'stock': stock
		})

	socketio.emit('request_response', data)

	return jsonify({"message": "Response received!"}), 200


"""Receive new request from listening thread and update requests list"""
@app.route("/new_request", methods=["POST"])
def new_request():
	data = request.json
	if data is None:
		return jsonify({"error": "Invalid JSON or no JSON provided"}), 400

	# JSON data exctraction
	uuid = data["uuid"]
	requester_node = data["requester_node"]
	product_id = data["product_id"]
	stock = data["stock"]

	# Validate all fields
	if not all([requester_node, product_id, stock]):
		return jsonify({"error": "Missing required fields"}), 400

	node.cursor.execute("SELECT id FROM products WHERE id = %s;", (product_id,))
	if node.cursor.rowcount == 0:
		return jsonify({"error": "Product requested is not registered, consequently request is removed"}), 404
	try:
		node.cursor.execute("INSERT INTO requests VALUES(%s, %s, %s, %s);", (uuid, requester_node, product_id, stock))

		node.db_conn.commit()
	except Exception as e:
		node.db_conn.rollback()
		return jsonify({"error": f"Error inserting to table in new_request: {e}"}), 400

	with node.lock:
		node.requests_cache.append({
			'uuid': uuid,
			'requester_node': requester_node,
			'product_id': product_id,
			'stock': stock
		})
		print(f"New request added to node{id(node)} request list {id(node.requests_cache)}; UUID: {uuid}, Requester: {requester_node}, Product: {product_id}, Quantity; {stock}")

	socketio.emit('new_request', data)

	try:
		# Reconnect with RabbitMQ
		if not node.publish_connection or node.publish_connection.is_closed:
			print("Closed connection. Trying to open it . . .")
			node.publish_connection = pika.BlockingConnection(pika.ConnectionParameters(node.url))
		if not node.publish_channel or node.publish_channel.is_closed:
			print("Closed channel. Trying create new one . . .")
			node.publish_channel = node.publish_connection.channel()

		message = {"uuid": uuid, "destination_node": node.id, "product_id": product_id, "stock": stock}
		node.publish_channel.basic_publish(
				exchange='',
				routing_key=requester_node + "_requests",
				body=json.dumps(message),
				properties=pika.BasicProperties(headers={'message_type': 'response'})
		) 

	except pika.exceptions.AMQPChannelError as e:
		print(f"Error in publish_channel: {e}")
	except pika.exceptions.AMQPConnectionError as e:
		print(f"Error in publish_connection: {e}")
	except Exception as e:
		print(f"Error sending request to {requester_node}: ({e})")

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
		node.cursor.execute("SELECT * FROM products WHERE id = %s;", (product_id,))
		if node.cursor.rowcount == 0:
			return jsonify({"error": f"No product found with id {product_id}"}), 405

		node.cursor.execute("SELECT * FROM inventory WHERE product_id = %s;", (product_id,))
		if node.cursor.rowcount == 0:
			node.cursor.execute("INSERT INTO inventory VALUES (%s, %s);", (product_id, stock))
		else:
			node.cursor.execute("UPDATE inventory SET stock = stock + %s WHERE product_id = %s;", (stock, product_id))

		node.cursor.execute("INSERT INTO transactions VALUES (%s, %s, %s, %s, NOW())", (seller, node.id, product_id, stock))

		node.db_conn.commit()

		with node.lock:
			node.cursor.execute("SELECT * FROM transactions ORDER BY date DESC LIMIT 1;")
			row = node.cursor.fetchone()
			if row is not None:
				node.transactions_cache.append(
					{"sender": str(row[0]), "receiver": str(row[1]), "product_id": str(row[2]), "stock": row[3], "date":str(row[4])}
				)

			if str(product_id) in node.inventory_cache:
				node.inventory_cache[str(product_id)] += stock
			else:
				node.cursor.execute("SELECT stock FROM inventory WHERE product_id = %s;", (product_id,))
				result = node.cursor.fetchone()
				if result:
					node.inventory_cache[str(product_id)] = result[0]

		message = f"Added {stock} units of {product_id} to inventory from {seller}."

		node.cursor.execute("SELECT minimum_stock FROM products WHERE id = %s;", (product_id,))
		result = node.cursor.fetchone()
		if result:
			minimum_stock = result[0];
			if minimum_stock >= node.inventory_cache[str(product_id)]:
				message += f"\nWARNING: {product_id} is at minimum stock levels!"

		return jsonify({"message": message}), 200
	except Exception as e:
		node.db_conn.rollback()
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
		node.cursor.execute("SELECT * FROM products WHERE id = %s;", (product_id,))
		if node.cursor.rowcount == 0:
			return jsonify({"error": f"No product found with id {product_id}"}), 405

		node.cursor.execute("SELECT stock FROM inventory WHERE product_id = %s;", (product_id,))
		result = node.cursor.fetchone()
		if result:
			product_stock = result[0]
			if stock > product_stock:
				node.db_conn.rollback()
				return jsonify({"error": f"Not enough stock for {product_id}"}), 400
			elif stock == product_stock:
				node.cursor.execute("DELETE FROM inventory WHERE product_id = %s;", (product_id,))
			else:
				node.cursor.execute("UPDATE inventory SET stock = stock - %s WHERE product_id = %s;", (stock, product_id))

			node.cursor.execute("INSERT INTO transactions VALUES (%s, %s, %s, %s, NOW())", (node.id, client, product_id, stock))
		
			node.db_conn.commit()

			with node.lock:
				node.cursor.execute("SELECT * FROM transactions ORDER BY date DESC LIMIT 1;")
				row = node.cursor.fetchone()
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

			message = f"Sold {stock} units of {product_id} to inventory to {client}."

			node.cursor.execute("SELECT minimum_stock FROM products WHERE id = %s;", (product_id,))
			result = node.cursor.fetchone()
			if result:
				minimum_stock = result[0];
				if minimum_stock >= node.inventory_cache[str(product_id)]:
					message += f"\nWARNING: {product_id} is at minimum stock levels!"

			return jsonify({"message": message}), 200
		else:
			node.db_conn.rollback()
			return jsonify({"error": f"Product {product_id} not found in inventory table"}), 404

	except Exception as e:
		node.db_conn.rollback()
		return jsonify({"error": f"Intern unexpected server error selling: {e}"}), 500


@app.route("/send_query", methods=["POST"])
def send_query():
	try:
		data = request.json
		if data is None:
			return jsonify({"error": "Invalid JSON or no JSON provided"}), 400

		destination_node = data["destination_node"] + "_queries"
		product_id = data["product_id"]
		stock = int(data["stock"])

		if not all ([destination_node, product_id, stock]):
			return jsonify({"error": "Missing required fields"}), 400

		print(f"Sending query to {destination_node} for {product_id} ({stock} units)")
		node.send_query(destination_node=destination_node, product_id=product_id, stock=stock)

		return jsonify({"message": f"Query for {product_id} sent to {destination_node} ({stock} units)"}), 200
	except Exception as e:
		return jsonify({"error": f"Query failed!"}), 400
 

@app.route("/send_request", methods=["POST"])
def send_request():
	# Send a request to another node
	try:
		data = request.json
		if data is None:
			return jsonify({"error": "Invalid JSON or no JSON provided"}), 400
		
		destination_node = data["destination_node"] + "_requests"
		product = data["product_id"]
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
	minimum_stock = data["minimum_stock"]
	unit_price = float(data["unit_price"])
	weight = float(data["weight"])
	expiration_date = datetime.strptime(data["expiration_date"], '%Y-%m-%d')

	if not all([id, name, description, minimum_stock, unit_price, weight, expiration_date]):
		return jsonify({"error": "Missing required fields"}), 400

	try:
		node.cursor.execute("INSERT INTO products (id, name, description, minimum_stock, unit_price, weight, expiration_date) VALUES (%s, %s, %s, %s, %s, %s, %s);", (id, name, description, minimum_stock, unit_price, weight, expiration_date))
		node.db_conn.commit()

		with node.lock:
			node.products_cache.append({'id': id, 'name': name, 'description': description, 'minimum_stock': minimum_stock, 'unit_price': unit_price, 'weight': weight, 'expiration_date': str(expiration_date)})

		return jsonify({"message": f"New product ({name}) added"}), 200
	except errors.UniqueViolation:
		node.db_conn.rollback()
		return jsonify({"error": f"ID {id} product already exists!"}), 409
	except Exception as e:
		node.db_conn.rollback()
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
		node.cursor.execute("DELETE FROM inventory WHERE product_id = %s;", (id,))
		node.cursor.execute("DELETE FROM products WHERE id = %s;", (id,))
		node.db_conn.commit()

		with node.lock:
			node.inventory_cache.pop(id)
			for i, item in enumerate(node.products_cache):
				if item.get("id") == id:
					node.products_cache.pop(i)
					break

		if node.cursor.rowcount == 0:
			return jsonify({"error": f"No product found with id {id}"}), 404

		return jsonify({"message": f"Product {id} deleted from products table and inventory table"}), 200
	except Exception as e:
		node.db_conn.rollback()
		return jsonify({"error": f"Intern unexpected server error deleting: {e}"}), 500


@app.route("/api/inventory", methods=["GET"])
def get_inventory():
	inventory = {product_id: stock for product_id, stock in node.inventory_cache.items()}
	print(inventory)

	if len(inventory) > 0:
		for product in node.products_cache:
			product_id = product.get("id")
			minimum_stock = product.get("minimum_stock")
			current_stock = node.inventory_cache.get(str(product_id))
			
			if minimum_stock is not None:
				inventory[product_id] = (current_stock, minimum_stock)

	return jsonify(inventory), 200

@app.route("/api/products", methods=["GET"])
def get_products():
	print(f"Products: { node.products_cache }")
	return jsonify(node.products_cache), 200

@app.route("/api/requests", methods=["GET"])
def get_requests():
	print(f"Current requests in node{id(node)}: {node.requests_cache}")
	return jsonify(node.requests_cache), 200


@app.route("/api/my_requests", methods=["GET"])
def get_my_requests():
	print(f"My current requests: {node.my_requests_cache}")
	return jsonify(node.my_requests_cache), 200


@app.route("/api/transactions", methods=["GET"])
def get_transactions():
	print(f"Transactions: { node.transactions_cache }")
	return jsonify(node.transactions_cache), 200


@app.route("/stop", methods=["POST"])
def stop():
	# Stop the node
	try:
		node.stop_listening()
		if requests_listening_thread and requests_listening_thread.is_alive():
			requests_listening_thread.join()
		node.cursor.close()
		node.db_conn.close()
	except Exception as e:
		print(f"Error closing features: {e}")
	finally:
		print("Bye bye!")
	return jsonify({"message": "Node stopped"}), 200

def signalHandler(sig, _):
	print("Bye bye!")
	try:
		node.stop_listening()
		if requests_listening_thread and requests_listening_thread.is_alive():
			requests_listening_thread.join()
	except Exception as e:
		print(f"Error closing features: {e}")
	finally:
		node.cursor.close()
		node.db_conn.close()
		sys.exit(0)

# Assign singal SIGNIT (Ctrl + ^C) to the function
signal.signal(signal.SIGINT, signalHandler)
signal.signal(signal.SIGTERM, signalHandler)

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument('--id', required=True, help='Node ID')
	parser.add_argument('--port', required=True, help='Port for the node')
	args = parser.parse_args()

	# Create the node object
	node = Node(id=args.id, url='localhost', port=args.port) 
	print(f"Node initialized with ID: {id(node)}, requests queue ID: {id(node.requests_cache)}, PORT: {node.port}")

	# Start listening in a thread
	requests_listening_thread = threading.Thread(target=node.start_listening_requests, daemon=True).start()
	queries_listening_thread = threading.Thread(target=node.start_listening_queries, daemon=True).start()

	app.run(debug=True, host="0.0.0.0", port=args.port)#, use_reloader=False)

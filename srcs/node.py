import pika
import json
import argparse
import threading

class Node:
    def __init__(self, name, request_queue, response_queue):
        self.name = name
        self.request_queue = request_queue
        self.response_queue = response_queue
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        self.channel = self.connection.channel()

        # Declare the queues
        self.channel.queue_declare(queue=self.request_queue)
        self.channel.queue_declare(queue=self.response_queue)

        # Local inventory for the node
        self.inventory = {}

    def add_item(self, product, quantity):
        """Add or update an item in the inventory"""
        if product in self.inventory:
            self.inventory[product] += quantity
        else:
            self.inventory[product] = quantity
        print(f"[{self.name}] Added {quantity} units of {product} to inventory.")

    def list_inventory(self):
        """List the current inventory"""
        print(f"[{self.name}] Current Inventory:")
        for product, quantity in self.inventory.items():
            print(f"  - {product}: {quantity} units")

    def handle_request(self, ch, method, properties, body):
        """Handle a request received in the request queue"""
        message = json.loads(body)
        product = message.get("product")
        origin_node = message.get("origin_node")

        print(f"[{self.name}] Request received from {origin_node} for {product}")

        # Check local inventory
        quantity = self.inventory.get(product, 0)

        # Send a response
        response = {"destination_node": origin_node, "product": product, "quantity": quantity}
        self.channel.basic_publish(exchange='', routing_key=origin_node, body=json.dumps(response))
        print(f"[{self.name}] Response sent to {origin_node}: {quantity} units of {product}")

    def send_request(self, destination_node, product):
        """Send a request to another node"""
        print(f"[{self.name}] Sending request to {destination_node} for {product}")
        message = {"origin_node": self.response_queue, "product": product}
        self.channel.basic_publish(exchange='', routing_key=destination_node, body=json.dumps(message))

    def handle_response(self, ch, method, properties, body):
        """Handle a response received from another node"""
        response = json.loads(body)
        product = response.get("product")
        quantity = response.get("quantity")
        print(f"[{self.name}] Response received: {quantity} units of {product}")

    def start_listening(self):
        """Start listening on both the request and response queues"""
        # Listen for requests
        self.channel.basic_consume(queue=self.request_queue, on_message_callback=self.handle_request, auto_ack=True)

        # Listen for responses
        self.channel.basic_consume(queue=self.response_queue, on_message_callback=self.handle_response, auto_ack=True)

        print(f"[{self.name}] Listening on queues '{self.request_queue}' and '{self.response_queue}'...")
        self.channel.start_consuming()

    def start_menu(self):
        """Display a menu for interactive functionality"""
        while True:
            print(f"\n[{self.name}] MENU:")
            print("1. Add Item to Inventory")
            print("2. List Inventory")
            print("3. Send Request to Another Node")
            print("4. Exit")
            choice = input("Choose an option: ")

            if choice == "1":
                product = input("Enter product name: ")
                quantity = int(input("Enter quantity: "))
                self.add_item(product, quantity)

            elif choice == "2":
                self.list_inventory()

            elif choice == "3":
                destination = input("Enter destination node queue: ")
                product = input("Enter product to query: ")
                self.send_request(destination_node=destination, product=product)

            elif choice == "4":
                print(f"[{self.name}] Exiting...")
                self.connection.close()
                break

            else:
                print("Invalid option. Please try again.")

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Distributed Inventory Node")
    parser.add_argument("--name", required=True, help="Name of the node")
    parser.add_argument("--request_queue", required=True, help="Request queue for the node")
    parser.add_argument("--response_queue", required=True, help="Response queue for the node")
    args = parser.parse_args()

    # Create a node
    node = Node(name=args.name, request_queue=args.request_queue, response_queue=args.response_queue)

    # Add some inventory items for testing
    node.add_item("Product A", 100)
    node.add_item("Product B", 50)

    # Start the listening thread
    threading.Thread(target=node.start_listening, daemon=True).start()

    # Start the interactive menu
    node.start_menu()


if __name__ == "__main__":
    main()

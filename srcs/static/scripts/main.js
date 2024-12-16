// Function to fetch and update the inventory
function updateInventory() {
	$.get("/show_inventory", function(data) {
		let inventoryList = '';
		for(let product in data) {
			inventoryList += `<li>${product}: ${data[product]} units</li>`;
		}
		$('#inventory-list').html(inventoryList);
	});
}

// Function update requests list
function updateRequests() {
	$.get("/show_requests", function(data) {
		let requestList = '';
		data.forEach(function(item) {
			requestList += `<li>Requester Node: ${item.requester_node}, Product: ${item.product}, Quantity: ${item.quantity}</li>`;
		});

		$('#requests-list').html(requestList);
	});
}

// Handle buying a product
$('#buy-form').on('submit', function(e) {
	e.preventDefault();
	const seller = $('#seller-buy').val();
	const product = $('#product-buy').val();
	const quantity = $('#quantity-buy').val();
	$.ajax({
		url: '/buy',
		method: 'POST',
		contentType: 'application/json',
		data: JSON.stringify({ seller: seller, product: product, quantity: quantity }),
		success: function(response) {
			alert(response.message);
			updateInventory();  // Update inventory after buying
		}
	});
});

// Handle selling a product
$('#sell-form').on('submit', function(e) {
	e.preventDefault();
	const client = $('#client-sell').val();
	const product = $('#product-sell').val();
	const quantity = $('#quantity-sell').val();
	$.ajax({
		url: '/sell',
		method: 'POST',
		contentType: 'application/json',
		data: JSON.stringify({ client: client, product: product, quantity: quantity }),
		success: function(response) {
			alert(response.message);
			updateInventory();  // Update inventory after selling
		},
		error: function(response) {
			alert(response.responseJSON.error);
		}
	});
});

// Handle sending a manual notification
$('#send-request-form').on('submit', function(e) {
	e.preventDefault();
	const destination_node = $('#node-id-request').val();
	const product = $('#product-request').val();
	const quantity = $('#quantity-request').val();
	$.ajax({
		url: '/send_request',
		method: 'POST',
		contentType: 'application/json',
		data: JSON.stringify({ destination_node: destination_node, product: product, quantity: quantity }),
		success: function(response) {
			alert(response.message);
		},
		error: function(response) {
			alert(response.responseJSON.error);
		}
	});
});

// Initial call to update inventory and notifications (also in case web is refreshed)
updateInventory();
updateRequests();

// Interval of long polling to append new requests
setInterval(updateRequests, 60000)

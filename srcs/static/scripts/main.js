// Function to fetch and update the inventory
function updateInventory() {
	$.get("/inventory", function(data) {
		let inventoryList = '';
		for (let product in data) {
			inventoryList += `<li>${product}: ${data[product]} units</li>`;
		}
		$('#inventory-list').html(inventoryList);
	});
}

// Function to fetch and update notifications
function updateRequests() {
	$.get("/requests", function(data) {
		let requestsList = '';
		$('#requests-list').empty();
		for (let request in data) {
			requestsList += `<li>${data[request]}</li>`;
		}
		if (requestsList) {
			$('#requests-list').html(requestsList);
		} else {
			$('#requests-list').append('<li>No new requests</li>');
		}
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
			updateRequests();  // Check for new notifications
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
		data: JSON.stringify({ product: product, quantity: quantity }),
		success: function(response) {
			alert(response.message);
			updateInventory();  // Update inventory after selling
			updateRequests();  // Check for new notifications
		},
		error: function(response) {
			alert(response.responseJSON.error);
		}
	});
});

// Handle sending a manual notification
$('#send-request-form').on('submit', function(e) {
	e.preventDefault();
	const node = $('#node-request').val();
	const product = $('#product-request').val();
	const quantity = $('#quantity-request').val();
	$.ajax({
		url: '/send_request',
		method: 'POST',
		contentType: 'application/json',
		data: JSON.stringify({ node: node, product: product, quantity: quantity }),
		success: function(response) {
			alert(response.message);
			updateRequests();  // Update notifications after sending a new one
		}
	});
});

// Initial call to update inventory and notifications
updateInventory();
updateRequests();

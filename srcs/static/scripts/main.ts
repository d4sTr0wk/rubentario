// Type definition for product request
interface ProductRequest {
  requester_node: string;
  product: string;
  stock: number;
}

// Type definition for product
interface Product {
  product_id: string;
  name: string;
  description: string;
  unit_price: number;
  weight: number;
  expiration_date: string;
}

// Function to fetch and update the inventory
function updateInventory(): void {
  $.get("/get_inventory", function (data: { [key: string]: number }) {
    let inventoryList = '';
    for (let product in data) {
      inventoryList += `<li>${product}: ${data[product]} units</li>`;
    }
    $('#inventory-list').html(inventoryList);
  });
}

// Function update requests list
function updateRequests(): void {
  $.get("/get_requests", function (data: ProductRequest[]) {
    let requestList = '';
    data.forEach(function (item) {
      requestList += `<li>Requester Node: ${item.requester_node}, Product: ${item.product}, Quantity: ${item.stock}</li>`;
    });

    $('#requests-list').html(requestList);
  });
}

// Add product to database
$('#add-product-form').on('submit', function (e: JQuery.SubmitEvent) {
  e.preventDefault();
  const product_id = $('#add-product-id').val() as string;
  const name = $('#add-product-name').val() as string;
  const description = $('#add-product-description').val() as string;
  const unit_price = parseFloat($('#add-product-unit-price').val() as string);
  const weight = parseFloat($('#add-product-weight').val() as string);
  const expiration_date = $('#add-product-expiration-date').val() as string;
  
  const productData: Product = {
    product_id,
    name,
    description,
    unit_price,
    weight,
    expiration_date
  };

  $.ajax({
    url: '/add_product',
    method: 'POST',
    contentType: 'application/json',
    data: JSON.stringify(productData),
    success: function (response: { message: string }) {
      alert(response.message);
    },
    error: function (response: JQuery.jqXHR) {
      alert(response.responseJSON.error);
    }
  });
});

$('#delete-product-form').on('submit', function (e: JQuery.SubmitEvent) {
	e.preventDefault();
	const product_id = $('#delete-product-id').val() as string;

	$.ajax({
		url: '/delete_product',
		method: 'POST',
		contentType: 'application/json',
		data: JSON.stringify({ product_id }),
		success: function (response: { message: string}) {
			alert(response.message);
		},
		error: function (response: JQuery.jqXHR) {
			alert(response.responseJSON.error);
		}
	});
});

// Handle buying a product
$('#buy-form').on('submit', function (e: JQuery.SubmitEvent) {
  e.preventDefault();
  const seller = $('#seller-buy').val() as string;
  const product_id = $('#product-id-buy').val() as string;
  const stock = parseInt($('#stock-buy').val() as string);

  $.ajax({
    url: '/buy',
    method: 'POST',
    contentType: 'application/json',
    data: JSON.stringify({ seller, product_id, stock }),
    success: function (response: { message: string }) {
      alert(response.message);
      updateInventory();  // Update inventory after buying
    },
    error: function (response: JQuery.jqXHR) {
      alert(response.responseJSON.error);
    }
  });
});

// Handle selling a product
$('#sell-form').on('submit', function (e: JQuery.SubmitEvent) {
  e.preventDefault();
  const client = $('#client-sell').val() as string;
  const product_id = $('#product-id-sell').val() as string;
  const stock = parseInt($('#stock-sell').val() as string);

  $.ajax({
    url: '/sell',
    method: 'POST',
    contentType: 'application/json',
    data: JSON.stringify({ client, product_id, stock }),
    success: function (response: { message: string }) {
      alert(response.message);
      updateInventory();  // Update inventory after selling
    },
    error: function (response: JQuery.jqXHR) {
      alert(response.responseJSON.error);
    }
  });
});

// Handle sending a manual notification
$('#send-request-form').on('submit', function (e: JQuery.SubmitEvent) {
  e.preventDefault();
  const destination_node = $('#node-id-request').val() as string;
  const product = $('#product-request').val() as string;
  const stock = parseInt($('#stock-request').val() as string);

  $.ajax({
    url: '/send_request',
    method: 'POST',
    contentType: 'application/json',
    data: JSON.stringify({ destination_node, product, stock }),
    success: function (response: { message: string }) {
      alert(response.message);
    },
    error: function (response: JQuery.jqXHR) {
      alert(response.responseJSON.error);
    }
  });
});

// Initial call to update inventory and notifications (also in case web is refreshed)
updateInventory();
updateRequests();

// Interval of long polling to append new requests
setInterval(updateRequests, 60000);


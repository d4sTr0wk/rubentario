// Function to fetch and update the inventory
function updateInventory() {
    $.get("/get_inventory", function (data) {
        var inventoryList = '';
        for (var product in data) {
            inventoryList += "<li>Product ID: ".concat(product, " | Stock: ").concat(data[product], " units</li>");
        }
        $('#inventory-list').html(inventoryList);
    });
}
// Function update requests list
function updateRequests() {
    $.get("/get_requests", function (data) {
        var requestList = '';
        data.forEach(function (item) {
            requestList += "<li>Requester Node: ".concat(item.requester_node, " | Product: ").concat(item.product, " | Quantity: ").concat(item.stock, "</li>");
        });
        $('#requests-list').html(requestList);
    });
}
function updateTransactions() {
    $.get("/get_transactions", function (data) {
        var transactionList = '';
        data.forEach(function (item) {
            transactionList += "<li>Sender: ".concat(item.sender, " | Receiver: ").concat(item.receiver, " | Product: ").concat(item.product_id, " | Stock: ").concat(item.stock, "</li>");
        });
        $('#transactions-list').html(transactionList);
    });
}
// Add product to database
$('#add-product-form').on('submit', function (e) {
    e.preventDefault();
    var product_id = $('#add-product-id').val();
    var name = $('#add-product-name').val();
    var description = $('#add-product-description').val();
    //const description = description_input === '' ? null : description_input;
    var unit_price = parseFloat($('#add-product-unit-price').val());
    //const unit_price = unit_price_input === '' ? null: parseFloat(unit_price_input);
    var weight = parseFloat($('#add-product-weight').val());
    //const weight = weight_input === '' ? null : parseFloat(weight_input);
    var expiration_date = $('#add-product-expiration-date').val();
    //const expiration_date = expiration_date_input === '' ? null : expiration_date_input;
    var productData = {
        product_id: product_id,
        name: name,
        description: description,
        unit_price: unit_price,
        weight: weight,
        expiration_date: expiration_date
    };
    $.ajax({
        url: '/add_product',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(productData),
        success: function (response) {
            alert(response.message);
        },
        error: function (response) {
            alert(response.responseJSON.error);
        }
    });
});
$('#delete-product-form').on('submit', function (e) {
    e.preventDefault();
    var product_id = $('#delete-product-id').val();
    $.ajax({
        url: '/delete_product',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ product_id: product_id }),
        success: function (response) {
            alert(response.message);
        },
        error: function (response) {
            alert(response.responseJSON.error);
        }
    });
});
// Handle buying a product
$('#buy-form').on('submit', function (e) {
    e.preventDefault();
    var seller = $('#seller-buy').val();
    var product_id = $('#product-id-buy').val();
    var stock = parseInt($('#stock-buy').val());
    $.ajax({
        url: '/buy',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ seller: seller, product_id: product_id, stock: stock }),
        success: function (response) {
            alert(response.message);
            updateInventory(); // Update inventory after buying
            updateTransactions();
        },
        error: function (response) {
            alert(response.responseJSON.error);
        }
    });
});
// Handle selling a product
$('#sell-form').on('submit', function (e) {
    e.preventDefault();
    var client = $('#client-sell').val();
    var product_id = $('#product-id-sell').val();
    var stock = parseInt($('#stock-sell').val());
    $.ajax({
        url: '/sell',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ client: client, product_id: product_id, stock: stock }),
        success: function (response) {
            alert(response.message);
            updateInventory(); // Update inventory after selling
            updateTransactions();
        },
        error: function (response) {
            alert(response.responseJSON.error);
        }
    });
});
// Handle sending a manual notification
$('#send-request-form').on('submit', function (e) {
    e.preventDefault();
    var destination_node = $('#node-id-request').val();
    var product = $('#product-request').val();
    var stock = parseInt($('#stock-request').val());
    $.ajax({
        url: '/send_request',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ destination_node: destination_node, product: product, stock: stock }),
        success: function (response) {
            alert(response.message);
        },
        error: function (response) {
            alert(response.responseJSON.error);
        }
    });
});
// Initial call to update inventory and notifications (also in case web is refreshed)
updateInventory();
updateRequests();
updateTransactions();
// Interval of long polling to append new requests
setInterval(updateRequests, 60000);

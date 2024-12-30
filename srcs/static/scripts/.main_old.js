// Function to fetch and update the inventory
function updateInventory() {
    $.get("/show_inventory", function (data) {
        var inventoryList = '';
        for (var product in data) {
            inventoryList += "<li>".concat(product, ": ").concat(data[product], " units</li>");
        }
        $('#inventory-list').html(inventoryList);
    });
}
// Function update requests list
function updateRequests() {
    $.get("/show_requests", function (data) {
        var requestList = '';
        data.forEach(function (item) {
            requestList += "<li>Requester Node: ".concat(item.requester_node, ", Product: ").concat(item.product, ", Quantity: ").concat(item.stock, "</li>");
        });
        $('#requests-list').html(requestList);
    });
}
// Add product to database
$('#add-product-form').on('submit', function (e) {
    e.preventDefault();
    var product_id = $('#add-product-id').val();
    var name = $('#add-product-name').val();
    var description = $('#add-product-description').val();
    var unit_price = parseFloat($('#add-product-unit-price').val());
    var weight = parseFloat($('#add-product-weight').val());
    var expiration_date = $('#add-product-expiration-date').val();
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
// Handle buying a product
$('#buy-form').on('submit', function (e) {
    e.preventDefault();
    var seller = $('#seller-buy').val();
    var product = $('#product-buy').val();
    var stock = parseInt($('#stock-buy').val());
    $.ajax({
        url: '/buy',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ seller: seller, product: product, stock: stock }),
        success: function (response) {
            alert(response.message);
            updateInventory(); // Update inventory after buying
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
    var product = $('#product-sell').val();
    var stock = parseInt($('#stock-sell').val());
    $.ajax({
        url: '/sell',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ client: client, product: product, stock: stock }),
        success: function (response) {
            alert(response.message);
            updateInventory(); // Update inventory after selling
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
// Interval of long polling to append new requests
setInterval(updateRequests, 60000);

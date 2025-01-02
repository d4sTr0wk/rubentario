var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
// Function to fetch and update the inventory
function updateInventory() {
    $.get("/get_inventory", function (data) {
        let inventoryList = '';
        for (let product in data) {
            inventoryList += `<li>Product ID: ${product} | Stock: ${data[product]} units</li>`;
        }
        $('#inventory-list').html(inventoryList);
    });
}
// Function update requests list
function updateRequests() {
    $.get("/get_requests", function (data) {
        let requestList = '';
        data.forEach(function (item) {
            requestList += `<li>Requester Node: ${item.requester_node} | Product: ${item.product} | Quantity: ${item.stock}</li>`;
        });
        $('#requests-list').html(requestList);
    });
}
function fetchTransactions() {
    return __awaiter(this, void 0, void 0, function* () {
        const response = yield fetch('/api/transactions');
        if (!response.ok) {
            throw new Error(`Transaction read table error: ${response.statusText}`);
        }
        return response.json();
    });
}
function renderTable(transactions) {
    const tbody = document.querySelector('#transactionsTable tbody');
    if (!tbody)
        return;
    tbody.innerHTML = ''; // Limpiar la tabla antes de llenarla
    transactions.forEach((transaction) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${transaction.sender}</td>
            <td>${transaction.receiver}</td>
            <td>${transaction.product_id}</td>
            <td>${transaction.stock}</td>
            <td>${new Date(transaction.date).toLocaleString()}</td>
        `;
        tbody.appendChild(row);
    });
}
function updateTransactions() {
    return __awaiter(this, void 0, void 0, function* () {
        try {
            const transactions = yield fetchTransactions();
            renderTable(transactions);
        }
        catch (error) {
            console.error('Error getting transactions:', error);
        }
    });
}
//function updateTransactions(): void {
//	$.get("/api/transactions", function (data: Transaction[]) {
//		let transactionList = '';
//		data.forEach(function (item) {
//			transactionList += `<li>Sender: ${item.sender} | Receiver: ${item.receiver} | Product: ${item.product_id} | Stock: ${item.stock}</li>`
//		});
//
//		$('#transactions-list').html(transactionList);
//	});
//}
// Add product to database
$('#add-product-form').on('submit', function (e) {
    e.preventDefault();
    const product_id = $('#add-product-id').val();
    const name = $('#add-product-name').val();
    const description = $('#add-product-description').val();
    //const description = description_input === '' ? null : description_input;
    const unit_price = parseFloat($('#add-product-unit-price').val());
    //const unit_price = unit_price_input === '' ? null: parseFloat(unit_price_input);
    const weight = parseFloat($('#add-product-weight').val());
    //const weight = weight_input === '' ? null : parseFloat(weight_input);
    const expiration_date = $('#add-product-expiration-date').val();
    //const expiration_date = expiration_date_input === '' ? null : expiration_date_input;
    const productData = {
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
    const product_id = $('#delete-product-id').val();
    $.ajax({
        url: '/delete_product',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ product_id }),
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
    const seller = $('#seller-buy').val();
    const product_id = $('#product-id-buy').val();
    const stock = parseInt($('#stock-buy').val());
    $.ajax({
        url: '/buy',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ seller, product_id, stock }),
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
    const client = $('#client-sell').val();
    const product_id = $('#product-id-sell').val();
    const stock = parseInt($('#stock-sell').val());
    $.ajax({
        url: '/sell',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ client, product_id, stock }),
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
    const destination_node = $('#node-id-request').val();
    const product = $('#product-request').val();
    const stock = parseInt($('#stock-request').val());
    $.ajax({
        url: '/send_request',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ destination_node, product, stock }),
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

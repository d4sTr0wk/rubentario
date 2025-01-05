"use strict";
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const host = window.location.host;
const socket = io(`${protocol}//${host}`);
socket.on('query_response', (data) => {
    if (!data.product_id) {
        alert("Product not found on node's inventory");
    }
    else {
        alert(`Query response received: ${JSON.stringify(data)}`);
    }
});
// INVENTORY
function fetchInventory() {
    return __awaiter(this, void 0, void 0, function* () {
        const response = yield fetch('/api/inventory');
        if (!response.ok) {
            throw new Error(`Inventory read table error: ${response.statusText}`);
        }
        return response.json();
    });
}
function renderInventoryTable(inventory) {
    const tbody = document.querySelector('#inventoryTable tbody');
    if (!tbody)
        return;
    tbody.innerHTML = ''; // Limpiar la tabla antes de llenarla
    if (Object.keys(inventory).length === 0) {
        tbody.innerHTML = '<tr><td colspan="2">No inventory available</td></tr>';
        return;
    }
    for (const product_id in inventory) {
        const [stock, minimum_stock] = inventory[product_id];
        const row = document.createElement('tr');
        if (stock <= minimum_stock) {
            row.classList.add('low-stock');
        }
        row.innerHTML = `
			<td>${product_id}</td>
			<td>${stock}</td>
		`;
        tbody.appendChild(row);
    }
}
function updateInventory() {
    return __awaiter(this, void 0, void 0, function* () {
        try {
            const inventory = yield fetchInventory();
            renderInventoryTable(inventory);
        }
        catch (error) {
            console.error('Error getting inventory:', error);
        }
    });
}
// PRODUCTS
function fetchProducts() {
    return __awaiter(this, void 0, void 0, function* () {
        const response = yield fetch('/api/products');
        if (!response.ok) {
            throw new Error(`Product read table error: ${response.statusText}`);
        }
        return response.json();
    });
}
function renderProductsTable(products) {
    const tbody = document.querySelector('#productsTable tbody');
    if (!tbody)
        return;
    tbody.innerHTML = ''; // Limpiar la tabla antes de llenarla
    if (products.length === 0 || products.every(p => Object.keys(p).length === 0)) {
        tbody.innerHTML = '<tr><td colspan="7">No products available</td></tr>';
        return;
    }
    products.forEach((product) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${product.id}</td>
            <td>${product.name}</td>
            <td>${product.description}</td>
			<td>${product.minimum_stock}</td>
            <td>${product.unit_price}</td>
			<td>${product.weight}</td>
            <td>${new Date(product.expiration_date).toLocaleDateString()}</td>
        `;
        tbody.appendChild(row);
    });
}
function updateProducts() {
    return __awaiter(this, void 0, void 0, function* () {
        try {
            const products = yield fetchProducts();
            renderProductsTable(products);
        }
        catch (error) {
            console.error('Error getting products:', error);
        }
    });
}
// REQUESTS
function fetchRequests() {
    return __awaiter(this, void 0, void 0, function* () {
        const response = yield fetch('/api/requests');
        if (!response.ok) {
            throw new Error(`Product read table error: ${response.statusText}`);
        }
        return response.json();
    });
}
function renderRequestsTable(requests) {
    const tbody = document.querySelector('#requestsTable tbody');
    if (!tbody)
        return;
    tbody.innerHTML = ''; // Limpiar la tabla antes de llenarla
    if (requests.length === 0 || requests.every(r => Object.keys(r).length === 0)) {
        tbody.innerHTML = '<tr><td colspan="3">No requests available</td></tr>';
        return;
    }
    requests.forEach((request) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${request.requester_node}</td>
            <td>${request.product_id}</td>
            <td>${request.stock}</td>
        `;
        tbody.appendChild(row);
    });
}
function updateRequests() {
    return __awaiter(this, void 0, void 0, function* () {
        try {
            const request = yield fetchRequests();
            renderRequestsTable(request);
        }
        catch (error) {
            console.error('Error getting requests:', error);
        }
    });
}
// TRANSACTIONS
function fetchTransactions() {
    return __awaiter(this, void 0, void 0, function* () {
        const response = yield fetch('/api/transactions');
        if (!response.ok) {
            throw new Error(`Transaction read table error: ${response.statusText}`);
        }
        return response.json();
    });
}
function renderTransactionsTable(transactions) {
    const tbody = document.querySelector('#transactionsTable tbody');
    if (!tbody)
        return;
    tbody.innerHTML = ''; // Limpiar la tabla antes de llenarla
    if (transactions.length === 0 || transactions.every(t => Object.keys(t).length === 0)) {
        tbody.innerHTML = '<tr><td colspan="5">No transactions available</td></tr>';
        return;
    }
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
            renderTransactionsTable(transactions);
        }
        catch (error) {
            console.error('Error getting transactions:', error);
        }
    });
}
// Add product to database
$('#add-product-form').on('submit', function (e) {
    e.preventDefault();
    const id = $('#add-product-id').val();
    const name = $('#add-product-name').val();
    const description = $('#add-product-description').val();
    //const description = description_input === '' ? null : description_input;
    const minimum_stock = parseInt($('#add-product-minimum-stock').val());
    const unit_price = parseFloat($('#add-product-unit-price').val());
    //const unit_price = unit_price_input === '' ? null: parseFloat(unit_price_input);
    const weight = parseFloat($('#add-product-weight').val());
    //const weight = weight_input === '' ? null : parseFloat(weight_input);
    const expiration_date = $('#add-product-expiration-date').val();
    //const expiration_date = expiration_date_input === '' ? null : expiration_date_input;
    const productData = {
        id,
        name,
        description,
        minimum_stock,
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
            updateProducts();
            alert(response.message);
        },
        error: function (response) {
            alert(response.responseJSON.error);
        }
    });
});
$('#delete-product-form').on('submit', function (e) {
    e.preventDefault();
    const id = $('#delete-product-id').val();
    $.ajax({
        url: '/delete_product',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ id }),
        success: function (response) {
            updateProducts();
            updateInventory();
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
$('#send-query-form').on('submit', function (e) {
    e.preventDefault();
    const destination_node = $('#destination-node-query').val();
    const product_id = $('#product-id-query').val();
    const stock = parseInt($('#stock-query').val());
    $.ajax({
        url: '/send_query',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ destination_node, product_id, stock }),
        success: function (response) {
            alert(response.message);
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
    const product_id = $('#product-request').val();
    const stock = parseInt($('#stock-request').val());
    $.ajax({
        url: '/send_request',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ destination_node, product_id, stock }),
        success: function (response) {
            alert(response.message);
        },
        error: function (response) {
            alert(response.responseJSON.error);
        }
    });
});
// Initial calls
updateInventory();
updateProducts();
updateRequests();
updateTransactions();
// Interval of long polling to append new requests
setInterval(updateRequests, 60000);
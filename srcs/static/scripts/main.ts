declare var io: any;

interface QueryResponse {
	product_id: string;
	stock: number;
	minimum_stock: number;
}

const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const host = window.location.host;
const socket = io(`${protocol}//${host}`);




interface InventoryDict {
	[product_id: string]: [number, number];
}

// Type definition for product
interface Product {
  id: string;
  name: string;
  description: string;
  minimum_stock: number;
  unit_price: number;
  weight: number;
  expiration_date: string;
}

// Type definition for request
interface Request {
	uuid: string;
	node: string;
	product_id: string;
	stock: number;
}

// Type definition for transaction
interface Transaction {
	sender: string;
	receiver: string;
	product_id: string;
	stock: number;
	date: string;
}

// INVENTORY
async function fetchInventory(): Promise<InventoryDict> {
	const response = await fetch('/api/inventory');
	if (!response.ok) {
		throw new Error(`Inventory read table error: ${response.statusText}`);
	}
	return response.json();
}

function renderInventoryTable(inventory: InventoryDict): void {
	const tbody = document.querySelector('#inventoryTable tbody');
    if (!tbody) return;

    tbody.innerHTML = ''; // Limpiar la tabla antes de llenarla

	if (Object.keys(inventory).length === 0) {
        tbody.innerHTML = '<tr><td colspan="2">No inventory available</td></tr>';
        return;
    }

	for (const product_id in inventory) {
		const [ stock, minimum_stock ] = inventory[product_id];
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


async function updateInventory(): Promise<void> {
    try {
        const inventory = await fetchInventory();
        renderInventoryTable(inventory);
    } catch (error) {
        console.error('Error getting inventory:', error);
    }
}


// PRODUCTS
async function fetchProducts(): Promise<Product[]> {
	const response = await fetch('/api/products');
	if (!response.ok) {
		throw new Error(`Product read table error: ${response.statusText}`);
	}
	return response.json();
}

function renderProductsTable(products: Product[]): void {
	const tbody = document.querySelector('#productsTable tbody');
    if (!tbody) return;

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

async function updateProducts(): Promise<void> {
    try {
        const products = await fetchProducts();
        renderProductsTable(products);
    } catch (error) {
        console.error('Error getting products:', error);
    }
}


// MY REQUESTS
async function fetchMyRequests(): Promise<Request[]> {
	const response = await fetch('/api/my_requests');
	if (!response.ok) {
		throw new Error(`Product read table error: ${response.statusText}`);
	}
	return response.json();
}

function renderMyRequestsTable(requests: Request[]): void {
	const tbody = document.querySelector('#myRequestsTable tbody');
    if (!tbody) return;

    tbody.innerHTML = ''; // Limpiar la tabla antes de llenarla

	if (requests.length === 0 || requests.every(r => Object.keys(r).length === 0)) {
        tbody.innerHTML = '<tr><td colspan="4">No requests available</td></tr>';
        return;
    }

    requests.forEach((request) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${request.uuid}</td>
            <td>${request.node}</td>
            <td>${request.product_id}</td>
            <td>${request.stock}</td>
        `;
        tbody.appendChild(row);
    });
}

async function updateMyRequests(): Promise<void> {
    try {
        const request = await fetchMyRequests();
        renderMyRequestsTable(request);
    } catch (error) {
        console.error('Error getting requests:', error);
    }
}


// OTHER'S REQUESTS
async function fetchRequests(): Promise<Request[]> {
	const response = await fetch('/api/requests');
	if (!response.ok) {
		throw new Error(`Product read table error: ${response.statusText}`);
	}
	return response.json();
}

function renderRequestsTable(requests: Request[]): void {
	const tbody = document.querySelector('#requestsTable tbody');
    if (!tbody) return;

    tbody.innerHTML = ''; // Limpiar la tabla antes de llenarla

	if (requests.length === 0 || requests.every(r => Object.keys(r).length === 0)) {
        tbody.innerHTML = '<tr><td colspan="4">No requests available</td></tr>';
        return;
    }

    requests.forEach((request) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${request.uuid}</td>
            <td>${request.node}</td>
            <td>${request.product_id}</td>
            <td>${request.stock}</td>
        `;
        tbody.appendChild(row);
    });
}

async function updateRequests(): Promise<void> {
    try {
        const request = await fetchRequests();
        renderRequestsTable(request);
    } catch (error) {
        console.error('Error getting requests:', error);
    }
}


// TRANSACTIONS
async function fetchTransactions(): Promise<Transaction[]> {
	const response = await fetch('/api/transactions');
	if (!response.ok) {
		throw new Error(`Transaction read table error: ${response.statusText}`);
	}
	return response.json();
}

function renderTransactionsTable(transactions: Transaction[]): void {
	const tbody = document.querySelector('#transactionsTable tbody');
    if (!tbody) return;

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

async function updateTransactions(): Promise<void> {
    try {
        const transactions = await fetchTransactions();
        renderTransactionsTable(transactions);
    } catch (error) {
        console.error('Error getting transactions:', error);
    }
}

// Add product to database
$('#add-product-form').on('submit', function (e: JQuery.SubmitEvent) {
  e.preventDefault();
  const id = $('#add-product-id').val() as string;
  const name = $('#add-product-name').val() as string;

  const description = $('#add-product-description').val() as string;
  //const description = description_input === '' ? null : description_input;

  const minimum_stock = parseInt($('#add-product-minimum-stock').val() as string);

  const unit_price = parseFloat($('#add-product-unit-price').val() as string);
  //const unit_price = unit_price_input === '' ? null: parseFloat(unit_price_input);

  const weight = parseFloat($('#add-product-weight').val() as string);
  //const weight = weight_input === '' ? null : parseFloat(weight_input);

  const expiration_date = $('#add-product-expiration-date').val() as string;
  //const expiration_date = expiration_date_input === '' ? null : expiration_date_input;

  const productData: Product = {
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
    success: function (response: { message: string }) {
		updateProducts();
		alert(response.message);
	},
    error: function (response: JQuery.jqXHR) {
		alert(response.responseJSON.error);
    }
  });
});

$('#delete-product-form').on('submit', function (e: JQuery.SubmitEvent) {
	e.preventDefault();
	const id = $('#delete-product-id').val() as string;

	$.ajax({
		url: '/delete_product',
		method: 'POST',
		contentType: 'application/json',
		data: JSON.stringify({ id }),
		success: function (response: { message: string}) {
			updateProducts();
			updateInventory();
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
	  updateTransactions();
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
	  updateTransactions();
    },
    error: function (response: JQuery.jqXHR) {
      alert(response.responseJSON.error);
    }
  });
});


// Handle sending a manual notification
$('#send-query-form').on('submit', function (e: JQuery.SubmitEvent) {
  e.preventDefault();
  const destination_node = $('#destination-node-query').val() as string;
  const product_id = $('#product-id-query').val() as string;
  const stock = parseInt($('#stock-query').val() as string);

  $.ajax({
    url: '/send_query',
    method: 'POST',
    contentType: 'application/json',
    data: JSON.stringify({ destination_node, product_id, stock }),
    success: function (response: { message: string }) {
      alert(response.message);
    },
    error: function (response: JQuery.jqXHR) {
      alert(response.responseJSON.error);
    }
  });
});


// Handle sending a manual notification
$('#send-request-form').on('submit', function (e: JQuery.SubmitEvent) {
  e.preventDefault();
  const destination_node = $('#destination-node-request').val() as string;
  const product_id = $('#product-id-request').val() as string;
  const stock = parseInt($('#stock-request').val() as string);
  $.ajax({
    url: '/send_request',
    method: 'POST',
    contentType: 'application/json',
    data: JSON.stringify({ destination_node, product_id, stock }),
    success: function (response: { message: string }) {
      alert(response.message);
    },
    error: function (response: JQuery.jqXHR) {
      alert(response.responseJSON.error);
    }
  });
});


// SOCKETS
socket.on('request_response', (data: Request) => {
	if (!data.product_id) {
		alert("Product not found on node's inventory");
	} else {
		updateMyRequests();
		alert(`Request acknowledged: ${JSON.stringify(data)}`)
	}
});

socket.on('new_request', (data: Request) => {
	updateRequests();
	alert(`Request received!: ${JSON.stringify(data)}`)
});

socket.on('query_response', (data: QueryResponse) => {
	if (!data.product_id) {
		alert("Product not found on node's inventory");
	} else {
		alert(`Query response received: ${JSON.stringify(data)}`)
	}
});


// Initial calls
updateInventory();
updateProducts();
updateMyRequests();
updateRequests();
updateTransactions();
// Interval of long polling to append new requests
setInterval(updateRequests, 60000);


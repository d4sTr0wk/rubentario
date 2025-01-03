// Type definition for product request
interface ProductRequest {
  requester_node: string;
  product: string;
  stock: number;
}

interface InventoryDict {
	[product_id: string]: number;
}

// Type definition for product
interface Product {
  id: string;
  name: string;
  description: string;
  unit_price: number;
  weight: number;
  expiration_date: string;
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
	console.log(response);
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
		const stock = inventory[product_id];
		const row = document.createElement('tr');
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
        tbody.innerHTML = '<tr><td colspan="6">No products available</td></tr>';
        return;
    }

    products.forEach((product) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${product.id}</td>
            <td>${product.name}</td>
            <td>${product.description}</td>
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


// REQUESTS
function updateRequests(): void {
  $.get("/api/requests", function (data: ProductRequest[]) {
    let requestList = '';
    data.forEach(function (item) {
      requestList += `<li>Requester Node: ${item.requester_node} | Product: ${item.product} | Quantity: ${item.stock}</li>`;
    });

    $('#requests-list').html(requestList);
  });
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
updateProducts();
updateRequests();
updateTransactions();
// Interval of long polling to append new requests
setInterval(updateRequests, 60000);


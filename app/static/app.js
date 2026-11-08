const apiStatus = document.querySelector("#api-status");
const statusDot = document.querySelector(".status-dot");
const productsTable = document.querySelector("#products-table-body");
const movementsTable = document.querySelector("#movements-table-body");

async function getJson(path) {
	const response = await fetch(path);

	if (!response.ok) {
		throw new Error(`Request failed: ${path}`);
	}

	return response.json();
}

function addCell(row, value) {
	const cell = document.createElement("td");
	cell.textContent = value;
	row.appendChild(cell);
}

function renderProducts(products, lowStockProducts) {
	const lowStockSkus = new Set(
		lowStockProducts.map((product) => product.sku)
	);

	productsTable.replaceChildren();

	for (const product of products) {
		const row = document.createElement("tr");
		addCell(row, product.sku);
		addCell(row, product.name);
		addCell(row, product.category);
		addCell(row, product.quantity_on_hand.toLocaleString("en-US"));
		addCell(row, product.reorder_point.toLocaleString("en-US"));

		const statusCell = document.createElement("td");
		const badge = document.createElement("span");
		const isLowStock = lowStockSkus.has(product.sku);

		badge.className = isLowStock
			? "stock-badge is-low"
			: "stock-badge is-ok";
		badge.textContent = isLowStock ? "Low stock" : "In stock";

		statusCell.appendChild(badge);
		row.appendChild(statusCell);
		productsTable.appendChild(row);
	}
}

async function loadDashboard() {
	try {
		const [products, balances, lowStockProducts, locations, movements] =
			await Promise.all([
				getJson("/products"),
				getJson("/inventory/by-location"),
				getJson("/products/low-stock"),
				getJson("/locations"),
				getJson("/inventory/movements"),
			]);

		const totalStock = balances.reduce(
			(total, balance) => total + balance.quantity,
			0
		);

		document.querySelector("#product-count").textContent =
			products.length.toLocaleString("en-US");
		document.querySelector("#stock-count").textContent =
			totalStock.toLocaleString("en-US");
		document.querySelector("#low-stock-count").textContent =
			lowStockProducts.length.toLocaleString("en-US");
		document.querySelector("#location-count").textContent =
			locations.length.toLocaleString("en-US");
		document.querySelector("#table-count").textContent =
			`${products.length} products`;

		renderProducts(products, lowStockProducts);
		renderMovements(movements);

		apiStatus.textContent = "Connected";
		statusDot.classList.add("is-connected");
	} catch (error) {
		apiStatus.textContent = "Unavailable";
		statusDot.classList.add("is-error");

		const row = document.createElement("tr");
		const cell = document.createElement("td");
		cell.colSpan = 6;
		cell.className = "empty-state";
		cell.textContent = "Could not load data from the API.";
		row.appendChild(cell);
		productsTable.replaceChildren(row);

		console.error(error);
	}
}

const transferForm = document.querySelector("#transfer-form");
const transferMessage = document.querySelector("#transfer-message");
const transferButton = transferForm.querySelector("button[type='submit']");

transferForm.addEventListener("submit", async (event) => {
	event.preventDefault();

	const formData = new FormData(transferForm);
	const requestBody = {
		sku: formData.get("sku").trim(),
		source_location_code: formData
			.get("source_location_code")
			.trim(),
		destination_location_code: formData
			.get("destination_location_code")
			.trim(),
		quantity: Number(formData.get("quantity")),
	};

	transferButton.disabled = true;
	transferMessage.className = "form-message";
	transferMessage.textContent = "Sending transfer…";

	try {
		const response = await fetch("/inventory/transfer", {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
			},
			body: JSON.stringify(requestBody),
		});
		const result = await response.json();

		if (!response.ok) {
			throw new Error(result.detail || "Transfer failed");
		}

		transferMessage.classList.add("is-success");
		transferMessage.textContent =
			`${result.quantity_transferred} units of ${result.sku} transferred.`;

		transferForm.reset();
		await loadDashboard();
	} catch (error) {
		transferMessage.classList.add("is-error");
		transferMessage.textContent = error.message;
	} finally {
		transferButton.disabled = false;
	}
});

const receiveForm = document.querySelector("#receive-form");
const receiveMessage = document.querySelector("#receive-message");
const receiveButton = receiveForm.querySelector("button[type='submit']");

receiveForm.addEventListener("submit", async (event) => {
	event.preventDefault();

	const formData = new FormData(receiveForm);
	const requestBody = {
		sku: formData.get("sku").trim(),
		location_code: formData.get("location_code").trim(),
		quantity: Number(formData.get("quantity")),
	};

	receiveButton.disabled = true;
	receiveMessage.className = "form-message";
	receiveMessage.textContent = "Sending receipt…";

	try {
		const response = await fetch("/inventory/receive", {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
			},
			body: JSON.stringify(requestBody),
		});
		const result = await response.json();

		if (!response.ok) {
			throw new Error(result.detail || "Receipt failed");
		}

		receiveMessage.classList.add("is-success");
		receiveMessage.textContent =
			`${result.quantity_received} units of ${result.sku} received.`;

		receiveForm.reset();
		await loadDashboard();
	} catch (error) {
		receiveMessage.classList.add("is-error");
		receiveMessage.textContent = error.message;
	} finally {
		receiveButton.disabled = false;
	}
});

function renderMovements(movements) {
	document.querySelector("#movement-count").textContent =
		`${movements.length} movements`;
	movementsTable.replaceChildren();

	if (movements.length === 0) {
		const row = document.createElement("tr");
		const cell = document.createElement("td");
		cell.colSpan = 6;
		cell.className = "empty-state";
		cell.textContent = "No inventory movements yet.";
		row.appendChild(cell);
		movementsTable.appendChild(row);
		return;
	}

	for (const movement of movements) {
		const row = document.createElement("tr");
		addCell(row, movement.sku);
		addCell(row, movement.movement_type);
		addCell(row, movement.location_code);
		addCell(row, movement.destination_location_code || "—");
		addCell(row, movement.quantity.toLocaleString("en-US"));
		addCell(row, movement.created_at);
		movementsTable.appendChild(row);
	}
}

loadDashboard();
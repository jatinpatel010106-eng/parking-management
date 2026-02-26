// Shared helper to show bootstrap-like alert messages
function showMessage(targetId, message, type = "info") {
    const target = document.getElementById(targetId);
    if (!target) return;
    target.innerHTML = `<div class="alert alert-${type} py-2">${message}</div>`;
}

async function apiRequest(url, method = "GET", data = null) {
    const options = { method, headers: {} };
    if (data) {
        options.headers["Content-Type"] = "application/json";
        options.body = JSON.stringify(data);
    }

    const response = await fetch(url, options);
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
        throw new Error(payload.error || "Something went wrong.");
    }
    return payload;
}

// -------- Login page --------
const loginForm = document.getElementById("loginForm");
if (loginForm) {
    loginForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        const formData = new FormData(loginForm);
        const email = formData.get("email")?.trim();
        const password = formData.get("password")?.trim();

        if (!email || !password) {
            showMessage("loginMessage", "Please fill all fields.", "danger");
            return;
        }

        try {
            const data = await apiRequest("/login", "POST", { email, password });
            showMessage("loginMessage", data.message, "success");
            setTimeout(() => {
                window.location.href = data.redirect || "/dashboard";
            }, 700);
        } catch (error) {
            showMessage("loginMessage", error.message, "danger");
        }
    });
}

// -------- Register page --------
const registerForm = document.getElementById("registerForm");
if (registerForm) {
    registerForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        const formData = new FormData(registerForm);
        const username = formData.get("username")?.trim();
        const email = formData.get("email")?.trim();
        const password = formData.get("password")?.trim();

        if (!username || !email || !password) {
            showMessage("registerMessage", "All fields are required.", "danger");
            return;
        }

        if (password.length < 6) {
            showMessage("registerMessage", "Password must be at least 6 characters.", "danger");
            return;
        }

        try {
            const data = await apiRequest("/register", "POST", { username, email, password });
            showMessage("registerMessage", data.message, "success");
            registerForm.reset();
        } catch (error) {
            showMessage("registerMessage", error.message, "danger");
        }
    });
}

// -------- Dashboard page --------
const addVehicleForm = document.getElementById("addVehicleForm");
const exitVehicleForm = document.getElementById("exitVehicleForm");
const vehiclesTableBody = document.querySelector("#vehiclesTable tbody");

async function loadVehicles(searchNumber = "") {
    if (!vehiclesTableBody) return;

    try {
        const query = searchNumber ? `?number=${encodeURIComponent(searchNumber)}` : "";
        const vehicles = await apiRequest(`/vehicles${query}`);
        vehiclesTableBody.innerHTML = "";

        if (!vehicles.length) {
            vehiclesTableBody.innerHTML = `<tr><td colspan="6" class="text-center text-muted">No parked vehicles found.</td></tr>`;
            return;
        }

        vehicles.forEach((vehicle) => {
            const row = document.createElement("tr");
            row.innerHTML = `
                <td>${vehicle.vehicle_number}</td>
                <td>${vehicle.owner_name}</td>
                <td>${vehicle.vehicle_type}</td>
                <td>${new Date(vehicle.entry_time).toLocaleString()}</td>
                <td><span class="badge bg-success">${vehicle.status}</span></td>
                <td><button class="btn btn-sm btn-danger" data-id="${vehicle.id}">Delete</button></td>
            `;
            row.querySelector("button")?.addEventListener("click", () => deleteVehicle(vehicle.id));
            vehiclesTableBody.appendChild(row);
        });
    } catch (error) {
        showMessage("globalMessage", error.message, "danger");
    }
}

async function deleteVehicle(vehicleId) {
    if (!confirm("Delete this vehicle record?")) return;

    try {
        const data = await apiRequest(`/vehicles/${vehicleId}`, "DELETE");
        showMessage("globalMessage", data.message, "success");
        loadVehicles();
    } catch (error) {
        showMessage("globalMessage", error.message, "danger");
    }
}

if (addVehicleForm) {
    addVehicleForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        const formData = new FormData(addVehicleForm);
        const payload = {
            owner_name: formData.get("owner_name")?.trim(),
            vehicle_number: formData.get("vehicle_number")?.trim(),
            vehicle_type: formData.get("vehicle_type")?.trim(),
        };

        try {
            const data = await apiRequest("/add_vehicle", "POST", payload);
            showMessage("globalMessage", `${data.message} Entry at ${new Date(data.entry_time).toLocaleString()}`, "success");
            addVehicleForm.reset();
            loadVehicles();
        } catch (error) {
            showMessage("globalMessage", error.message, "danger");
        }
    });
}

if (exitVehicleForm) {
    exitVehicleForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        const formData = new FormData(exitVehicleForm);
        const payload = {
            vehicle_number: formData.get("vehicle_number")?.trim(),
        };

        try {
            const data = await apiRequest("/exit_vehicle", "POST", payload);
            showMessage(
                "globalMessage",
                `${data.message} Duration: ${data.duration_hours} hour(s). Fee: ₹${data.total_fee}`,
                "success"
            );
            exitVehicleForm.reset();
            loadVehicles();
        } catch (error) {
            showMessage("globalMessage", error.message, "danger");
        }
    });
}

const refreshBtn = document.getElementById("refreshVehiclesBtn");
refreshBtn?.addEventListener("click", () => loadVehicles());

document.getElementById("searchVehicleBtn")?.addEventListener("click", () => {
    const searchNumber = document.getElementById("searchVehicleInput")?.value?.trim() || "";
    loadVehicles(searchNumber);
});

// Admin tools
async function loadUsers() {
    try {
        const users = await apiRequest("/admin/users");
        const usersList = document.getElementById("usersList");
        if (!usersList) return;
        usersList.innerHTML = "";
        users.forEach((user) => {
            const li = document.createElement("li");
            li.className = "list-group-item";
            li.innerHTML = `<strong>${user.username}</strong> - ${user.email} <small>(${user.role})</small>`;
            usersList.appendChild(li);
        });
    } catch (error) {
        showMessage("globalMessage", error.message, "danger");
    }
}

async function loadHistory() {
    try {
        const data = await apiRequest("/admin/history");
        const historyList = document.getElementById("historyList");
        const earningsSummary = document.getElementById("earningsSummary");
        if (!historyList || !earningsSummary) return;

        earningsSummary.classList.remove("d-none");
        earningsSummary.textContent = `Total Earnings: ₹${data.total_earnings}`;

        historyList.innerHTML = "";
        data.history.forEach((item) => {
            const li = document.createElement("li");
            li.className = "list-group-item";
            li.innerHTML = `<strong>${item.vehicle_number}</strong> (${item.vehicle_type}) - ₹${item.total_fee}<br><small>${new Date(item.entry_time).toLocaleString()} → ${new Date(item.exit_time).toLocaleString()}</small>`;
            historyList.appendChild(li);
        });
    } catch (error) {
        showMessage("globalMessage", error.message, "danger");
    }
}

document.getElementById("loadUsersBtn")?.addEventListener("click", loadUsers);
document.getElementById("loadHistoryBtn")?.addEventListener("click", loadHistory);

if (vehiclesTableBody) {
    loadVehicles();
}

const API = "/customer-service/api/customers";


const registerForm = document.getElementById("registerForm");

if (registerForm) {

    registerForm.addEventListener("submit", async function(event) {

        event.preventDefault();

        const message = document.getElementById("registerMessage");

        const request = {
            firstName: document.getElementById("firstName").value,
            lastName: document.getElementById("lastName").value,
            email: document.getElementById("registerEmail").value,
            password: document.getElementById("registerPassword").value
        };

        try {

            const response = await fetch(`${API}/register`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(request)
            });

            if (!response.ok) {
                throw new Error("Registration failed");
            }

            const data = await response.json();

            message.textContent = "Registration successful. Redirecting to login...";

            setTimeout(() => {
                window.location.href = "index.html";
            }, 1200);

        } catch (error) {

            message.textContent =
                "Registration failed. Email may already be registered.";

        }

    });

}


const loginForm = document.getElementById("loginForm");

if (loginForm) {

    loginForm.addEventListener("submit", async function(event) {

        event.preventDefault();

        const message = document.getElementById("loginMessage");

        const request = {
            email: document.getElementById("loginEmail").value,
            password: document.getElementById("loginPassword").value
        };

        try {

            const response = await fetch(`${API}/login`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(request)
            });

            if (!response.ok) {
                throw new Error("Login failed");
            }

            const data = await response.json();

            localStorage.setItem(
                "customerId",
                data.customerId
            );

            localStorage.setItem(
                "customerName",
                data.firstName
            );

            window.location.href = "dashboard.html";

        } catch (error) {

            message.textContent =
                "Invalid email or password";

        }

    });

}


const customerName =
    document.getElementById("customerName");

if (customerName) {

    const name =
        localStorage.getItem("customerName");

    if (!name) {

        window.location.href = "index.html";

    } else {

        customerName.textContent = name;

    }

}


function logout() {

    localStorage.clear();

    window.location.href = "index.html";

}

const accountNumberElement =
    document.getElementById("accountNumber");

const accountBalanceElement =
    document.getElementById("accountBalance");

if (accountNumberElement && accountBalanceElement) {

    const customerId =
        localStorage.getItem("customerId");

    if (customerId) {

        loadAccount(customerId);

    } else {

        window.location.href = "index.html";
    }
}


async function loadAccount(customerId) {

    try {

        const response = await fetch(
            `/account-service/api/accounts/customer/${customerId}`
        );

        if (!response.ok) {
            throw new Error("Unable to load account");
        }

        const account = await response.json();

        accountNumberElement.textContent =
            account.accountNumber;

        accountBalanceElement.textContent =
            `₹${Number(account.balance).toFixed(2)}`;

    } catch (error) {

        accountNumberElement.textContent =
            "Unable to load";

        accountBalanceElement.textContent =
            "₹0.00";

        console.error(error);
    }
}

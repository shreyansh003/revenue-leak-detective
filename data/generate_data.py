import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

# -----------------------------
# SETTINGS
# -----------------------------

NUM_TRANSACTIONS = 50000

np.random.seed(42)
random.seed(42)

# -----------------------------
# BASIC VALUES
# -----------------------------

payment_methods = ["UPI", "CARD", "NETBANKING", "WALLET"]
devices = ["mobile", "desktop", "tablet"]
customer_types = ["new", "returning"]

failure_reasons = [
    "BANK_ERROR",
    "INSUFFICIENT_FUNDS",
    "TIMEOUT",
    "CARD_DECLINED"
]

# -----------------------------
# GENERATE CUSTOMERS
# -----------------------------

num_customers = 10000

customers = []

for i in range(num_customers):

    customer_id = f"C{i+1:05d}"

    customer_type = random.choices(
        customer_types,
        weights=[0.35, 0.65]
    )[0]

    customers.append({
        "customer_id": customer_id,
        "customer_type": customer_type
    })

customers_df = pd.DataFrame(customers)

# -----------------------------
# GENERATE TRANSACTIONS
# -----------------------------

transactions = []

start_date = datetime(2026, 8, 1)

for i in range(NUM_TRANSACTIONS):

    customer = random.choice(customers)

    customer_id = customer["customer_id"]
    customer_type = customer["customer_type"]

    # Transaction amount
    amount = round(
        np.random.lognormal(mean=7, sigma=0.8),
        2
    )

    # Keep amount reasonable
    amount = min(max(amount, 100), 50000)

    payment_method = random.choices(
        payment_methods,
        weights=[0.45, 0.35, 0.15, 0.05]
    )[0]

    device = random.choices(
        devices,
        weights=[0.70, 0.25, 0.05]
    )[0]

    # Random date/time
    random_minutes = random.randint(
        0,
        30 * 24 * 60
    )

    timestamp = start_date + timedelta(
        minutes=random_minutes
    )

    hour = timestamp.hour

    # -----------------------------
    # BASE FAILURE PROBABILITY
    # -----------------------------

    failure_probability = 0.05

    # -----------------------------
    # HIDDEN LEAK #1
    #
    # Mobile + UPI + 8PM-10PM
    # has unusually high failures
    # -----------------------------

    if (
        payment_method == "UPI"
        and device == "mobile"
        and 20 <= hour < 22
    ):
        failure_probability = 0.18

    # -----------------------------
    # OTHER NORMAL VARIATIONS
    # -----------------------------

    if payment_method == "CARD":
        failure_probability += 0.02

    if customer_type == "returning":
        failure_probability -= 0.01

    failure_probability = max(
        0.01,
        min(failure_probability, 0.30)
    )

    # -----------------------------
    # PAYMENT RESULT
    # -----------------------------

    failed = np.random.random() < failure_probability

    if failed:

        status = "failed"

        failure_reason = random.choices(
            failure_reasons,
            weights=[0.35, 0.25, 0.25, 0.15]
        )[0]

        retry_count = random.randint(0, 3)

    else:

        status = "success"
        failure_reason = None
        retry_count = 0

    # -----------------------------
    # CHECKOUT
    # -----------------------------

    checkout_started = True

    if status == "success":

        checkout_completed = True

    else:

        # Some failed transactions
        # are abandoned
        checkout_completed = (
            random.random() < 0.30
        )

    transactions.append({

        "transaction_id":
            f"TX{i+1:06d}",

        "customer_id":
            customer_id,

        "amount":
            amount,

        "payment_method":
            payment_method,

        "device":
            device,

        "timestamp":
            timestamp,

        "status":
            status,

        "failure_reason":
            failure_reason,

        "retry_count":
            retry_count,

        "customer_type":
            customer_type,

        "checkout_started":
            checkout_started,

        "checkout_completed":
            checkout_completed
    })

# -----------------------------
# CREATE DATAFRAME
# -----------------------------

df = pd.DataFrame(transactions)

# -----------------------------
# SAVE
# -----------------------------

df.to_csv(
    "data/transactions.csv",
    index=False
)

customers_df.to_csv(
    "data/customers.csv",
    index=False
)

print("Dataset generated successfully!")
print(f"Transactions: {len(df)}")
print(f"Customers: {len(customers_df)}")

print("\nStatus distribution:")
print(df["status"].value_counts())

print("\nPayment method distribution:")
print(df["payment_method"].value_counts())
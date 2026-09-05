````markdown
# 💰 Revenue Leak Detective

AI-powered revenue recovery investigation and decision system built for the Razorpay AI Builder Internship / Buildathon 2026.

## 🚨 Problem

Payment failures create hidden revenue leakage.

A failed payment alone does not tell us:

- Where the biggest revenue leak is
- What is causing the failures
- Whether similar failures historically recover
- Which recovery action should be attempted
- When the system should stop

## 💡 Solution

Revenue Leak Detective turns payment failure data into ranked, evidence-backed recovery opportunities.

```text
Payment Transactions
        ↓
Revenue Leak Detection
        ↓
Root Cause Investigation
        ↓
Historical Recovery Evidence
        ↓
Recovery Prediction
        ↓
Eligibility Rules
        ↓
Safety Guard
        ↓
EXECUTE / ESCALATE / STOP
        ↓
Audit Trail
        ↓
Batch Measurement
````

## 🔎 How It Works

### 1. Detect Revenue Leaks

The system analyzes:

* Payment method
* Device
* Hour of day
* Failure rate
* Failed revenue

It compares segment failure rates against a historical baseline and ranks suspicious segments.

### 2. Find the Root Cause

For each suspicious segment, the system identifies the failure reason responsible for the largest failed revenue.

Examples:

```text
BANK_ERROR
TIMEOUT
INSUFFICIENT_FUNDS
CARD_DECLINED
```

### 3. Historical Recovery Signal

The system checks historical transaction behavior to determine whether failed payments were followed by successful payments.

This produces a **Historical Recovery Signal**.

> This is observational evidence, not proof that an intervention caused recovery.

### 4. Predict Recovery

```text
Predicted Recovery
=
Root Cause Revenue
×
Historical Recovery Signal
```

### 5. Decide the Action

The system can make three decisions:

```text
EXECUTE
ESCALATE
STOP
```

Weak opportunities are stopped instead of blindly attempting recovery.

### 6. Safety Guard

Recovery actions are bounded by safety rules.

For example:

```text
Retry count = 0
      ↓
Retry allowed

Retry count >= 1
      ↓
STOP
```

### 7. Audit Trail

Every recovery decision is stored in PostgreSQL.

The audit trail records:

* Segment
* Root cause
* Recommended action
* Historical recovery signal
* Predicted recovery
* Guard decision
* Execution status

## 📊 Example Result

Synthetic dataset:

```text
Top Revenue Leak

UPI | mobile | 21:00

Failure Rate:          18.24%
Historical Baseline:    5.46%
Actual Failures:          112
Expected Failures:         34
Excess Failures:           78
Segment Revenue Risk: ₹169,058.58
```

Root cause investigation:

```text
Root Cause: BANK_ERROR

Root Cause Failures:       44
Root Cause Value:      ₹72,071.82

Historical Recovery Signal: 15.91%
Predicted Recovery:         ₹11,465.97

Recommended Action: RETRY_LATER
Final Decision: EXECUTE
```

All values above come from synthetic/test-mode data.

## 🖥️ Dashboard

The Streamlit dashboard provides:

* Latest recovery batch
* Revenue at risk
* Predicted recovery
* Simulated intervention recovery
* EXECUTE / ESCALATE / STOP decisions
* Top revenue leaks
* Root cause investigation
* Recovery opportunity ranking
* Prediction evaluation
* Recovery audit trail

## 🛠️ Technology Stack

* Python
* PostgreSQL
* SQL
* psycopg2
* Pandas
* Streamlit
* Rule-based decision engine
* Historical behavioral analysis

## 📁 Project Structure

```text
revenue-leak-detective/
│
├── data/
│   ├── customers.csv
│   └── transactions.csv
│
├── app/
│   ├── database.py
│   ├── test_connection.py
│   ├── detector.py
│   ├── root_cause.py
│   ├── recommender.py
│   ├── recovery_model.py
│   ├── action_guard.py
│   ├── audit_log.py
│   ├── opportunity_ranker.py
│   ├── eligibility.py
│   ├── recovery_simulator.py
│   ├── recovery_executor.py
│   ├── batch_recovery.py
│   └── dashboard.py
│
├── .env.example
├── .gitignore
└── README.md
```

## ⚙️ Setup

Install dependencies:

```bash
pip install psycopg2-binary python-dotenv pandas streamlit
```

Create a PostgreSQL database:

```text
revenue_leak_db
```

Create a `.env` file:

```text
DB_HOST=localhost
DB_PORT=5432
DB_NAME=revenue_leak_db
DB_USER=postgres
DB_PASSWORD=your_password
```

Never commit `.env` to GitHub.

## ▶️ Run

Detector:

```bash
python app/detector.py
```

Recovery opportunity ranking:

```bash
python app/opportunity_ranker.py
```

Dashboard:

```bash
streamlit run app/dashboard.py
```

## 🛡️ Safety & Test Mode

This is a prototype using synthetic/test-mode data.

**No real payment transactions are executed.**

Recovery outcomes are simulated for evaluation.

The project explicitly distinguishes:

* Historical observational evidence
* Predicted recovery
* Simulated intervention recovery

Simulated recovery must not be interpreted as real business recovery or causal evidence.

## 🎯 Core Idea

The goal is not simply:

> Find failed payments.

The goal is:

> **Find the most valuable revenue leaks, understand why they happen, estimate whether they are recoverable, choose bounded actions, and stop when the evidence is insufficient.**

## 🔮 Future Improvements

* Real-time payment event processing
* Customer-level recovery modeling
* Experiment-based causal measurement
* Learned intervention policies
* Human approval workflows
* Production payment-provider integration

## ⚠️ Disclaimer

This project is a prototype built using synthetic/test-mode data.

It does not perform real payment transactions and should not be used as a production payment recovery system without additional security, compliance, experimentation, and risk controls.

```

T

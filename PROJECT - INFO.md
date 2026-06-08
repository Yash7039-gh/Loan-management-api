A production-ready **REST API** built with **Python Flask**, **PostgreSQL**, **Docker**, and **Jenkins CI/CD**. 

Live Demo: https://yash7039-gh.github.io/Loan-management-api/

## ⚡ Quick Start

### Option 1 — Docker Compose (Recommended)
```bash
git clone https://github.com/Yash7039-gh/loan-management-api
cd loan-management-api
cp .env.example .env
docker-compose up --build
```
API runs at: `http://localhost:5000`

### Option 2 — Local Setup
```bash
# 1. Clone repo
git clone https://github.com/Yash7039-gh/loan-management-api
cd loan-management-api

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate       # Linux/Mac
venv\Scripts\activate          # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Setup PostgreSQL
# Create database: loandb
# Update .env with your credentials

# 5. Run the app
python app.py
```

---

## 🗄️ Database Schema

```sql
students (id, name, email, course, created_at)
    │
    └──< loans (id, student_id, amount, interest_rate,
                tenure_months, status, applied_at, approved_at, remarks)
                │
                └──< repayments (id, loan_id, amount_paid, paid_at, remarks)
```



## 📡 API Endpoints

### Students
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/students` | List all students |
| GET | `/api/students/:id` | Get student by ID |
| POST | `/api/students` | Create new student |
| PUT | `/api/students/:id` | Update student |
| DELETE | `/api/students/:id` | Delete student |

### Loans
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/loans` | List all loans |
| GET | `/api/loans?status=pending` | Filter by status |
| GET | `/api/loans/:id` | Get loan by ID |
| POST | `/api/loans` | Apply for loan |
| PATCH | `/api/loans/:id/status` | Approve/Reject/Close loan |

### Repayments
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/repayments` | Record repayment |
| GET | `/api/repayments/loan/:id` | Get repayments by loan |

### Dashboard
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/dashboard` | Get summary statistics |

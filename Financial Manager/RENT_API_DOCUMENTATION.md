# Rent Management Web Server - API Documentation

## Overview

The Rent Management Web Server provides a complete REST API for remote access to rent tracking data without modifying the existing desktop UI. It includes:

- **Read-only tenant status endpoints** for safe remote data access
- **Dispute management system** for tenants to file and track disputes
- **Monthly breakdown** for detailed payment tracking
- **Delinquency information** for account status monitoring
- **Complete data export** for integration with external systems

## Architecture

### Components

1. **rent_api.py** - Core API logic layer
   - `RentStatusAPI` - Read-only data provider
   - `Dispute` - Dispute model
   - `DisputeStatus`, `DisputeType` - Enumerations

2. **rent_web_server.py** - Flask REST server
   - `RentManagementServer` - HTTP endpoint handler
   - CORS-enabled for cross-origin requests

3. **rent_web_server_runner.py** - Server initialization
   - Standalone runner script
   - Integration utilities

4. **rent_web_client.py** - Python client library
   - `RentManagementClient` - Easy API access
   - Example usage code

### Data Flow

```
Desktop UI (RentTracker)
        ↓
  Financial Manager
        ↓
  rent_tracker.py (unchanged)
        ↓
  rent_api.py (read-only wrapper)
        ↓
  rent_web_server.py (Flask HTTP endpoints)
        ↓
  Web UI / Remote Clients
```

The desktop UI operates normally. The API layer reads from the same data without modification.

## Getting Started

### Installation

1. Ensure Flask and Flask-CORS are installed:
```bash
pip install flask flask-cors requests
```

2. Copy the API files to your Financial Manager `src/` directory:
   - `rent_api.py`
   - `rent_web_server.py`
   - `rent_web_server_runner.py`
   - `rent_web_client.py`

### Starting the Server

#### Option 1: Standalone Script
```bash
python src/rent_web_server_runner.py --port 5000
```

#### Option 2: In Your Application
```python
from src.rent_web_server_runner import run_rent_web_server
import threading

# Start in background thread
server_thread = threading.Thread(
    target=run_rent_web_server,
    args=(5000, False),
    daemon=True
)
server_thread.start()
```

#### Option 3: With Gunicorn (Production)
```bash
gunicorn -w 4 -b 0.0.0.0:5000 src.rent_web_server_runner:app
```

### Testing the Server

```python
from src.rent_web_client import create_client

client = create_client('http://localhost:5000')

# Check health
if client.health_check():
    print("Server is healthy!")

# Get all tenants
success, tenants = client.get_all_tenants()
if success:
    for tenant in tenants:
        print(f"- {tenant['name']}")
```

## API Endpoints

### Health & Status

#### GET `/api/health`
Check server health status.

**Response:**
```json
{
  "status": "healthy",
  "service": "rent-management-server",
  "timestamp": "2026-01-19T15:30:00.000000",
  "version": "1.0.0"
}
```

---

### Tenant Status Endpoints

#### GET `/api/tenants`
Get status for all tenants.

**Response:**
```json
{
  "status": "success",
  "count": 5,
  "tenants": [
    {
      "tenant_id": "T001",
      "name": "John Doe",
      "contact_info": {...},
      "account_status": "active",
      "rental_period": {...},
      "rent_amount": 1800.00,
      "payment_summary": {...},
      "delinquency_info": {...},
      ...
    }
  ],
  "timestamp": "2026-01-19T15:30:00.000000"
}
```

#### GET `/api/tenants/<tenant_id>`
Get comprehensive status for a specific tenant.

**Parameters:**
- `tenant_id` (path): Tenant ID

**Response:**
```json
{
  "status": "success",
  "data": {
    "tenant_id": "T001",
    "name": "John Doe",
    "contact_info": {
      "email": "john@example.com",
      "phone": "555-1234"
    },
    "account_status": "active",
    "rental_period": {
      "start_date": "2025-01-01",
      "end_date": "2026-12-31"
    },
    "rent_amount": 1800.00,
    "deposit_amount": 1800.00,
    "rent_due_date": 5,
    "notes": "Good tenant, pays on time",
    "payment_summary": {
      "total_rent_paid": 10800.00,
      "delinquency_balance": 0.00,
      "overpayment_credit": 200.00,
      "service_credit": 0.00,
      "payment_count": 6,
      "last_payment_date": "2026-01-05",
      "last_payment_amount": 1800.00,
      "delinquent_months": []
    },
    "delinquency_info": {
      "is_delinquent": false,
      "total_delinquency": 0.00,
      "delinquent_month_count": 0,
      "delinquent_months_detail": [],
      "requires_attention": false
    },
    "monthly_status": {
      "2025-12": "Paid in Full",
      "2026-01": "Paid in Full"
    },
    "overpayment_credit": 200.00,
    "service_credit": 0.00,
    "disputes": [],
    "last_modified": "2026-01-19T10:00:00.000000"
  },
  "timestamp": "2026-01-19T15:30:00.000000"
}
```

#### GET `/api/tenants/<tenant_id>/payment-summary`
Get payment summary for a tenant.

**Response:**
```json
{
  "status": "success",
  "data": {
    "total_rent_paid": 10800.00,
    "delinquency_balance": 0.00,
    "overpayment_credit": 200.00,
    "service_credit": 0.00,
    "payment_count": 6,
    "last_payment_date": "2026-01-05",
    "last_payment_amount": 1800.00,
    "delinquent_months": []
  },
  "timestamp": "2026-01-19T15:30:00.000000"
}
```

#### GET `/api/tenants/<tenant_id>/delinquency`
Get delinquency information for a tenant.

**Response:**
```json
{
  "status": "success",
  "data": {
    "is_delinquent": true,
    "total_delinquency": 1800.00,
    "delinquent_month_count": 1,
    "delinquent_months_detail": [
      {
        "year": 2026,
        "month": 1,
        "expected_rent": 1800.00,
        "status": "Delinquent"
      }
    ],
    "requires_attention": true
  },
  "timestamp": "2026-01-19T15:30:00.000000"
}
```

#### GET `/api/tenants/<tenant_id>/monthly-breakdown`
Get detailed monthly breakdown.

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "year": 2025,
      "month": 12,
      "month_key": "2025-12",
      "expected_rent": 1800.00,
      "paid_amount": 1800.00,
      "balance": 0.00,
      "status": "Paid in Full",
      "payment_date": "2025-12-05"
    },
    {
      "year": 2026,
      "month": 1,
      "month_key": "2026-01",
      "expected_rent": 1800.00,
      "paid_amount": 1800.00,
      "balance": 0.00,
      "status": "Paid in Full",
      "payment_date": "2026-01-05"
    }
  ],
  "count": 2,
  "timestamp": "2026-01-19T15:30:00.000000"
}
```

#### GET `/api/tenants/<tenant_id>/export`
Export complete tenant data snapshot.

**Response:**
```json
{
  "status": "success",
  "data": {
    "timestamp": "2026-01-19T15:30:00.000000",
    "tenant_status": {...},
    "payment_summary": {...},
    "monthly_breakdown": [...],
    "delinquency_info": {...},
    "disputes": [...]
  },
  "timestamp": "2026-01-19T15:30:00.000000"
}
```

---

### Dispute Endpoints

#### GET `/api/disputes`
Get all disputes across all tenants.

**Response:**
```json
{
  "status": "success",
  "count": 2,
  "disputes": [
    {
      "dispute_id": "DSP001",
      "tenant_id": "T001",
      "type": "payment_not_recorded",
      "description": "Payment made on 2026-01-15 not showing in records",
      "amount": 1800.00,
      "reference_month": [2026, 1],
      "created_by": "tenant_web_ui",
      "created_at": "2026-01-19T10:00:00.000000",
      "updated_at": "2026-01-19T10:00:00.000000",
      "status": "open",
      "admin_notes": null,
      "evidence_notes": "Bank transfer receipt available"
    }
  ],
  "timestamp": "2026-01-19T15:30:00.000000"
}
```

#### GET `/api/disputes/<dispute_id>`
Get specific dispute details.

**Parameters:**
- `dispute_id` (path): Dispute ID

**Response:**
```json
{
  "status": "success",
  "data": {
    "dispute_id": "DSP001",
    "tenant_id": "T001",
    "type": "payment_not_recorded",
    "description": "Payment made on 2026-01-15 not showing in records",
    "amount": 1800.00,
    "reference_month": [2026, 1],
    "created_by": "tenant_web_ui",
    "created_at": "2026-01-19T10:00:00.000000",
    "updated_at": "2026-01-19T10:00:00.000000",
    "status": "open",
    "admin_notes": null,
    "evidence_notes": "Bank transfer receipt available"
  },
  "timestamp": "2026-01-19T15:30:00.000000"
}
```

#### GET `/api/tenants/<tenant_id>/disputes`
Get all disputes for a specific tenant.

**Parameters:**
- `tenant_id` (path): Tenant ID

**Response:**
```json
{
  "status": "success",
  "count": 1,
  "disputes": [
    {
      "dispute_id": "DSP001",
      "tenant_id": "T001",
      ...
    }
  ],
  "timestamp": "2026-01-19T15:30:00.000000"
}
```

#### POST `/api/tenants/<tenant_id>/disputes`
Create a new dispute (tenant-initiated).

**Parameters:**
- `tenant_id` (path): Tenant ID

**Request Body:**
```json
{
  "dispute_type": "payment_not_recorded",
  "description": "Payment made on 2026-01-15 not showing in records",
  "amount": 1800.00,
  "reference_month": "2026-01",
  "evidence_notes": "Bank transfer receipt available"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Dispute created successfully",
  "dispute": {
    "dispute_id": "DSP001",
    "tenant_id": "T001",
    "type": "payment_not_recorded",
    "description": "Payment made on 2026-01-15 not showing in records",
    "amount": 1800.00,
    "reference_month": [2026, 1],
    "created_by": "tenant_web_ui",
    "created_at": "2026-01-19T15:30:00.000000",
    "updated_at": "2026-01-19T15:30:00.000000",
    "status": "open",
    "admin_notes": null,
    "evidence_notes": "Bank transfer receipt available"
  },
  "timestamp": "2026-01-19T15:30:00.000000"
}
```

#### PUT `/api/disputes/<dispute_id>/status`
Update dispute status (admin endpoint).

**Parameters:**
- `dispute_id` (path): Dispute ID

**Request Body:**
```json
{
  "status": "acknowledged",
  "admin_notes": "We found your payment and have corrected the balance"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Dispute status updated",
  "dispute": {
    "dispute_id": "DSP001",
    ...
    "status": "acknowledged",
    "updated_at": "2026-01-19T15:35:00.000000",
    "admin_notes": "We found your payment and have corrected the balance"
  },
  "timestamp": "2026-01-19T15:35:00.000000"
}
```

---

### Info Endpoints

#### GET `/api/info/dispute-types`
Get available dispute types for creating disputes.

**Response:**
```json
{
  "status": "success",
  "types": [
    {"value": "payment_not_recorded", "name": "Payment Not Recorded"},
    {"value": "incorrect_balance", "name": "Incorrect Balance"},
    {"value": "duplicate_charge", "name": "Duplicate Charge"},
    {"value": "overpayment_not_credited", "name": "Overpayment Not Credited"},
    {"value": "service_credit_error", "name": "Service Credit Error"},
    {"value": "other", "name": "Other"}
  ],
  "timestamp": "2026-01-19T15:30:00.000000"
}
```

#### GET `/api/info/dispute-statuses`
Get available dispute statuses.

**Response:**
```json
{
  "status": "success",
  "statuses": [
    {"value": "open", "name": "Open"},
    {"value": "acknowledged", "name": "Acknowledged"},
    {"value": "pending_review", "name": "Pending Review"},
    {"value": "resolved", "name": "Resolved"},
    {"value": "rejected", "name": "Rejected"}
  ],
  "timestamp": "2026-01-19T15:30:00.000000"
}
```

---

## Error Responses

All errors follow a consistent format:

```json
{
  "status": "error",
  "message": "Description of what went wrong",
  "timestamp": "2026-01-19T15:30:00.000000"
}
```

### Common Error Codes

| Code | Message | Cause |
|------|---------|-------|
| 400 | Bad Request | Missing or invalid parameters |
| 404 | Not Found | Resource (tenant, dispute) not found |
| 500 | Internal Server Error | Server-side error |

---

## Python Client Usage

### Basic Setup

```python
from src.rent_web_client import create_client

client = create_client('http://localhost:5000')

# Check if server is running
if client.health_check():
    print("Server is ready!")
```

### Getting Tenant Data

```python
# Get all tenants
success, tenants = client.get_all_tenants()
if success:
    for tenant in tenants:
        print(f"{tenant['name']}: {tenant['account_status']}")

# Get specific tenant
success, tenant = client.get_tenant('T001')
if success:
    print(f"Balance: ${tenant['payment_summary']['delinquency_balance']:.2f}")

# Get payment summary
success, summary = client.get_payment_summary('T001')
if success:
    print(f"Total Paid: ${summary['total_rent_paid']:.2f}")

# Get monthly breakdown
success, breakdown = client.get_monthly_breakdown('T001')
if success:
    for month in breakdown:
        print(f"{month['month_key']}: {month['status']}")
```

### Creating and Managing Disputes

```python
# Create a dispute
success, dispute = client.create_dispute(
    tenant_id='T001',
    dispute_type='payment_not_recorded',
    description='Payment not showing on 1/15/2026',
    amount=1800.00,
    reference_month=(2026, 1),
    evidence_notes='Bank receipt #12345'
)

if success:
    print(f"Dispute created: {dispute['dispute_id']}")

# Get tenant's disputes
success, disputes = client.get_tenant_disputes('T001')
if success:
    for dispute in disputes:
        print(f"{dispute['dispute_id']}: {dispute['status']}")

# Update dispute status (admin)
success, updated = client.update_dispute_status(
    dispute_id='DSP001',
    status='resolved',
    admin_notes='Payment found and applied'
)
```

---

## Integration Examples

### Example 1: Web Dashboard Integration

```python
from flask import Flask, render_template, jsonify
from src.rent_web_client import create_client

app = Flask(__name__)
client = create_client('http://localhost:5000')

@app.route('/dashboard/tenant/<tenant_id>')
def tenant_dashboard(tenant_id):
    success, tenant = client.get_tenant(tenant_id)
    if success:
        return render_template('tenant_dashboard.html', tenant=tenant)
    return "Tenant not found", 404
```

### Example 2: Regular Sync

```python
import threading
import time
from src.rent_web_client import create_client

def sync_tenant_data(tenant_id, callback):
    client = create_client('http://localhost:5000')
    
    while True:
        success, tenant = client.get_tenant(tenant_id)
        if success:
            callback(tenant)
        time.sleep(300)  # Every 5 minutes

# Start in background
sync_thread = threading.Thread(
    target=sync_tenant_data,
    args=('T001', lambda data: print(f"Updated: {data['payment_summary']}")),
    daemon=True
)
sync_thread.start()
```

---

## Security Considerations

1. **Authentication** (Future Feature)
   - Currently unauthenticated - suitable for internal networks
   - Plan to add JWT or OAuth in future version

2. **CORS**
   - Enabled for all origins by default
   - Configure for specific domains in production

3. **Sensitive Data**
   - All endpoints return read-only data
   - No password or sensitive credential exposure
   - Consider IP whitelisting in production

4. **Rate Limiting** (Recommended)
   - Implement rate limiting for public deployments
   - Use tools like Flask-Limiter

---

## Configuration

### Environment Variables (Optional)

```bash
RENT_API_HOST=0.0.0.0
RENT_API_PORT=5000
RENT_API_DEBUG=false
```

### Running with Gunicorn (Production)

```bash
gunicorn -w 4 \
  -b 0.0.0.0:5000 \
  --access-logfile - \
  --error-logfile - \
  --log-level info \
  src.rent_web_server_runner:app
```

---

## Troubleshooting

### Server won't start
- Check if port 5000 is already in use
- Verify RentTracker can initialize
- Check logs for import errors

### Disputes not persisting
- Disputes are stored in memory - restart clears them
- Consider adding database persistence for production

### CORS errors
- Ensure Flask-CORS is installed
- Check cross-origin headers in client

### Connection refused
- Verify server is running on specified host/port
- Check firewall rules
- Verify client is using correct URL

---

## Support

For issues or questions:
1. Check application logs in `financial_tracker.log`
2. Enable debug mode: `python src/rent_web_server_runner.py --debug`
3. Review error responses for specific issues


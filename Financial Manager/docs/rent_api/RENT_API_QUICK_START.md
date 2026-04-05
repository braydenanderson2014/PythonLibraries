# Rent Management API - Quick Integration Guide

## 5-Minute Setup

### 1. Install Dependencies
```bash
pip install flask flask-cors requests
```

### 2. Start the Server
```bash
# Option A: Standalone
python "Python Projects/Financial Manager/src/rent_web_server_runner.py" --port 5000

# Option B: From Python
from src.rent_web_server_runner import run_rent_web_server
import threading
threading.Thread(target=run_rent_web_server, args=(5000, False), daemon=True).start()
```

### 3. Test It Works
```bash
curl http://localhost:5000/api/health
```

Expected response:
```json
{"status": "healthy", "service": "rent-management-server", ...}
```

---

## Integration with Existing UI

The API runs **alongside** your existing desktop UI - no modifications needed:

```python
# Your main_window.py or application startup
from src.rent_web_server_runner import run_rent_web_server
import threading

# In your __init__ or startup function:
if __name__ == '__main__':
    # Start web server in background
    server_thread = threading.Thread(
        target=run_rent_web_server,
        args=(5000, False),
        daemon=True
    )
    server_thread.start()
    
    # Your existing UI code continues normally
    # RentTracker and all UI components work unchanged
    ...
```

---

## Quick API Examples

### Get Tenant Status
```bash
curl http://localhost:5000/api/tenants/T001
```

### Get All Tenants
```bash
curl http://localhost:5000/api/tenants
```

### Get Payment Summary
```bash
curl http://localhost:5000/api/tenants/T001/payment-summary
```

### Get Monthly Breakdown
```bash
curl http://localhost:5000/api/tenants/T001/monthly-breakdown
```

### Create a Dispute
```bash
curl -X POST http://localhost:5000/api/tenants/T001/disputes \
  -H "Content-Type: application/json" \
  -d '{
    "dispute_type": "payment_not_recorded",
    "description": "Payment made on 1/15 not showing",
    "amount": 1800.00,
    "reference_month": "2026-01"
  }'
```

### Get Disputes for Tenant
```bash
curl http://localhost:5000/api/tenants/T001/disputes
```

### Update Dispute Status (Admin)
```bash
curl -X PUT http://localhost:5000/api/disputes/DSP001/status \
  -H "Content-Type: application/json" \
  -d '{
    "status": "resolved",
    "admin_notes": "Payment found and applied to account"
  }'
```

---

## Python Client Examples

### Basic Usage
```python
from src.rent_web_client import create_client

client = create_client('http://localhost:5000')

# Health check
if client.health_check():
    print("✓ Server running")

# Get tenant
success, tenant = client.get_tenant('T001')
if success:
    print(f"Balance: ${tenant['payment_summary']['delinquency_balance']:.2f}")

# Get disputes
success, disputes = client.get_tenant_disputes('T001')
if success:
    for d in disputes:
        print(f"- {d['dispute_id']}: {d['status']}")
```

### Create Dispute
```python
from src.rent_web_client import create_client

client = create_client('http://localhost:5000')

success, dispute = client.create_dispute(
    tenant_id='T001',
    dispute_type='payment_not_recorded',
    description='Payment on 1/15/2026 not recorded',
    amount=1800.00,
    reference_month=(2026, 1)
)

if success:
    print(f"Created: {dispute['dispute_id']}")
```

### Update Dispute (Admin)
```python
success, updated = client.update_dispute_status(
    dispute_id='DSP001',
    status='resolved',
    admin_notes='Issue resolved - payment applied'
)
```

---

## API Endpoints Summary

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/health` | Health check |
| GET | `/api/tenants` | All tenants status |
| GET | `/api/tenants/<id>` | Specific tenant full status |
| GET | `/api/tenants/<id>/payment-summary` | Payment summary |
| GET | `/api/tenants/<id>/delinquency` | Delinquency info |
| GET | `/api/tenants/<id>/monthly-breakdown` | Monthly details |
| GET | `/api/tenants/<id>/export` | Full data export |
| GET | `/api/disputes` | All disputes |
| GET | `/api/disputes/<id>` | Specific dispute |
| GET | `/api/tenants/<id>/disputes` | Tenant's disputes |
| POST | `/api/tenants/<id>/disputes` | Create dispute |
| PUT | `/api/disputes/<id>/status` | Update dispute status |
| GET | `/api/info/dispute-types` | Available types |
| GET | `/api/info/dispute-statuses` | Available statuses |

---

## Dispute Types

When creating a dispute, use one of these types:

- `payment_not_recorded` - Payment made but not showing
- `incorrect_balance` - Balance calculated incorrectly
- `duplicate_charge` - Charged twice for same month
- `overpayment_not_credited` - Overpayment not applied
- `service_credit_error` - Service credit issue
- `other` - Other dispute type

---

## Dispute Statuses

Disputes progress through these statuses:

- `open` - Newly filed dispute
- `acknowledged` - Admin has seen and acknowledged
- `pending_review` - Under investigation
- `resolved` - Dispute resolved
- `rejected` - Dispute rejected

---

## Testing Checklist

- [ ] Server starts without errors
- [ ] `/api/health` returns healthy status
- [ ] `/api/tenants` returns tenant list
- [ ] `/api/tenants/<id>` returns specific tenant
- [ ] Create dispute endpoint works
- [ ] Update dispute status endpoint works
- [ ] Existing UI still functions normally
- [ ] No performance impact on desktop app

---

## Common Issues

### Port Already in Use
```python
# Use different port
python src/rent_web_server_runner.py --port 8000
```

### Import Errors
```bash
# Ensure in correct directory
cd "Python Projects/Financial Manager"
```

### Server Crashes
```python
# Enable debug mode to see errors
python src/rent_web_server_runner.py --debug
```

### CORS Errors
- Ensure `flask-cors` is installed
- API has CORS enabled by default

---

## Next Steps

1. **For Web UI**: Use `rent_web_client.py` to fetch data
2. **For Authentication**: Add JWT/OAuth in future version
3. **For Persistence**: Add database storage for disputes
4. **For Production**: Use Gunicorn or uWSGI instead of Flask dev server

---

## File Structure

```
Financial Manager/
├── src/
│   ├── rent_api.py                 # Core API logic
│   ├── rent_web_server.py          # Flask server
│   ├── rent_web_server_runner.py   # Server startup
│   ├── rent_web_client.py          # Python client
│   └── rent_tracker.py             # (unchanged)
├── RENT_API_DOCUMENTATION.md       # Full API docs
└── RENT_API_QUICK_START.md         # This file
```

---

## Support

- Check logs: `financial_tracker.log`
- Enable debug: `--debug` flag
- Review full docs: `RENT_API_DOCUMENTATION.md`


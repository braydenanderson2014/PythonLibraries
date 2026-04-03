 # Financial Manager
 
 Financial Manager is a PyQt6 desktop application that combines personal finance tracking, rent management, tenant analytics, POS tools, stock tracking, and related automation in one application shell.
 
 ## Run The App
 
 Install dependencies:
 
 ```bash
 pip install -r requirements.txt
 ```
 
 Start the current desktop entry point:
 
 ```bash
 python main_window.py
 ```
 
 The startup flow is:
 
 - `main_window.py` creates the Qt application and splash flow.
 - `ui/login.py` handles authentication.
 - `ui/main_window.py` builds the tabbed shell and menu system.
 
 ## Main Areas
 
 - `ui/financial_tracker.py`: financial dashboard and account tooling.
 - `ui/rent_dashboard_tab.py`: rent dashboard charts and tenant summary table.
 - `ui/rent_management_tab.py`: rent operations, payments, overrides, exports, and summaries.
 - `src/rent_tracker.py`: rent calculations, delinquency, overrides, and lease-status logic.
 - `src/tenant.py`: tenant JSON persistence.
 - `src/rent_db.py`: SQLite sync for rent reporting and history.
 
 ## Settings
 
 Application settings are available from `Edit > Settings` in the main window.
 
 Current settings exposed there:
 
 - Theme
 - Default rent amount
 - Default deposit amount
 - Default due day
 
 Store and tax administration remain under the `Admin` menu.
 
 ## Data Storage
 
 - In development, runtime data is written under `resources/`.
 - In packaged builds, runtime data is written to the per-user application-data directory resolved by `src/app_paths.py`.
 - General app settings are stored in `settings.json`.
 - Rent tenant data is stored in `tenants.json` and synced into `rent_data.db`.
 
 ## Notes
 
 - This README reflects the current desktop application rather than the original project template.
 - The repository also contains specialized rent API documentation and build scripts for deployment workflows.

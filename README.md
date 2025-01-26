# Water and Energy Log API

A FastAPI-based application for managing water and energy logs, providing endpoints for tracking, grouping, and exporting logs. It also includes user authentication using JWT tokens.

## Features

- User authentication with JWT tokens
- Create, read, update, delete water and energy logs
- Group logs by month and week
- Export logs as Excel files
- Retrieve total usage for today, this week, and this month

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/sarahuu/personal-resource-tracker-api.git
   cd yourproject
   ```

2. Set up a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r app/requirements.txt
   ```

4. Run migrations:
   ```bash
    alembic revision --autogenerate -m your-comment
   ```
   ```bash
   alembic upgrade head
   ```

5. Start the app:
   ```bash
   uvicorn app.main:app --reload
   ```

   The API will be available at `http://localhost:8001`.

## Some Endpoints
Check out `https://personal-resource-tracker-api.onrender.com/docs` for mor info
### Authentication

- `POST /token` - Login and receive JWT token

### Water Log Endpoints

- `POST /water-logs/` - Create a water log
- `GET /water-logs/logs-by-month` - Group water logs by months of the current year
- `GET /water-logs/logs-by-week` - Group water logs by days in current week

### Energy Log Endpoints

- `POST /energy-logs/` - Create an energy log
- `GET /enery-logs/logs-by-month` - Group energy logs by months of the current year
- `GET /energy-logs/logs-by-week` - Group energy logs by days in current week

### Export Endpoints

- `GET /export-water-logs-excel` - Export water logs to an Excel file
- `GET /export-energy-logs-excel` - Export energy logs to an Excel file

## License

MIT License

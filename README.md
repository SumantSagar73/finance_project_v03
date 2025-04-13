# Personal Finance Tracker

A simple and practical personal finance management application that helps users track their expenses, income, and savings.

## Features

- User authentication (signup/login)
- Dashboard with financial overview
- Expense and income tracking
- Basic budget management
- Transaction categorization
- Simple financial reports

## Setup Instructions

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file with:
```
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-secret-key
```

4. Initialize the database:
```bash
flask db init
flask db migrate
flask db upgrade
```

5. Run the application:
```bash
flask run
```

## Project Structure

```
finance_tracker/
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── routes.py
│   ├── forms.py
│   └── templates/
│       ├── base.html
│       ├── auth/
│       └── dashboard/
├── static/
│   ├── css/
│   └── js/
├── instance/
├── .env
├── config.py
└── app.py
``` 
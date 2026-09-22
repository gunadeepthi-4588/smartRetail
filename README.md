# SmartRetail — End-to-End Retail Inventory Intelligence & Demand Forecasting

A decision-support web platform for retail store owners that combines sales management, inventory tracking, ML demand forecasting, risk detection, and explainable reorder recommendations.

## Project Structure

```
smartRetail/
├── backend/
│   ├── app/
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   └── health.py
│   │   ├── models/
│   │   ├── services/
│   │   ├── utils/
│   │   └── __init__.py          # Flask application factory
│   ├── config.py                # Environment configuration classes
│   ├── requirements.txt         # Backend Python dependencies
│   ├── run.py                   # Development server entry point
│   ├── .env.example             # Backend environment template
│   └── .gitignore
│
├── frontend/
│   ├── src/
│   │   ├── components/          # Reusable UI widgets
│   │   ├── pages/               # Functional pages
│   │   ├── services/
│   │   │   └── api.js           # Centralized REST API client
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css            # Dark theme design system tokens
│   ├── package.json             # Vite + React dependencies
│   ├── vite.config.js           # Vite config with API proxy
│   ├── index.html
│   ├── .env.example             # Frontend environment template
│   └── .gitignore
│
├── .gitignore                   # Root gitignore
└── README.md
```

## Quickstart Setup

### Backend (Flask + Python)
1. Navigate to backend: `cd backend`
2. Create virtual environment: `python -m venv venv`
3. Activate: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Linux/Mac)
4. Install dependencies: `pip install -r requirements.txt`
5. Copy environment file: `cp .env.example .env`
6. Run: `python run.py`

### Frontend (React + Vite)
1. Navigate to frontend: `cd frontend`
2. Install packages: `npm install`
3. Copy environment file: `cp .env.example .env`
4. Run: `npm run dev`

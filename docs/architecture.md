# SmartRetail — System Architecture Overview

## Architecture Diagram

```
+-------------------------------------------------------------+
|                      Client Browser                         |
|  React 18 + Vite + Chart.js + Vanilla CSS Design System     |
|                      (Port 5173)                            |
+------------------------------+------------------------------+
                               |
                               | REST API (HTTP JSON)
                               v
+-------------------------------------------------------------+
|                   Flask REST API Server                     |
|            (Port 5000 - Application Factory)                |
|                                                             |
|  +------------------+  +-----------------+  +------------+  |
|  | Blueprints       |  | Services & ETL  |  | ML Engine  |  |
|  | /api/health      |  | Pandas & NumPy  |  | Scikit-    |  |
|  | (CRUD in Ph 5)   |  | (Ph 8-10)       |  | Learn      |  |
|  +------------------+  +-----------------+  +------------+  |
+------------------------------+------------------------------+
                               |
                               | PyMySQL Connection Pool
                               v
+-------------------------------------------------------------+
|                   MySQL Relational Database                 |
|             (Schema & Seed Data in Phase 3)                 |
+-------------------------------------------------------------+
```

## Security & Secrets Policy
- `.env` contains local development credentials and is excluded from git.
- `.env.example` serves as the public schema template.
- Frontend communicates exclusively via REST APIs and never connects directly to MySQL.

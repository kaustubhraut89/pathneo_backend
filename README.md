# Pathneo Backend Architecture

Pathneo is built using a modern, scalable **Microservices Architecture** powered by FastAPI. This repository contains the backend ecosystem designed to handle users, assessments, AI integrations, school management, and notifications in isolated, independently deployable services.

## 🏗️ Architecture Flow

The system is divided into domain-specific microservices that communicate with each other (via HTTP/REST or message queues, depending on the implementation).

```mermaid
graph TD
    Client[Client App (React/Next.js)] --> API_GW[API Gateway / Load Balancer]
    
    API_GW --> US[User Service :8000]
    API_GW --> AS[Assessment Service :8001]
    API_GW --> SS[School Service :8004]
    
    US -.-> NS[Notification Service :8002]
    AS -.-> AIS[AI Service :8003]
    
    US --- DB_Core[(Core MySQL DB)]
    AS --- DB_Core
    SS --- DB_Core
    
    AS --- Redis[(Redis Cache)]
    AIS --- Redis
    
    AIS --- OpenAI[OpenAI / Anthropic APIs]
    NS --- SMTP[SMTP / MSG91]
```

## 📦 Microservices Breakdown

| Service | Port | Description | Database / External deps |
|---------|------|-------------|--------------------------|
| **User Service** | `8000` | Core authentication, user management, RBAC, profiles. | MySQL |
| **Assessment Service** | `8001` | Handles tests, quizzes, scores, and evaluations. | MySQL, Redis |
| **Notification Service**| `8002` | Handles external communications (Emails via SMTP, SMS via MSG91). | None (Internal API) |
| **AI Service** | `8003` | Interfaces with LLMs (OpenAI/Anthropic) for grading or recommendations. | Redis, LLM APIs |
| **School Service** | `8004` | Manages school data, classes, institution-level analytics. | MySQL |

*(Note: There is also a legacy/monolithic `backend/` folder which may contain shared core logic or older migrations).*

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10+
- MySQL Server (Local or Remote)
- Redis Server (Local or Remote)

### 2. Setup Virtual Environment
It is highly recommended to run this project in a virtual environment.

```bash
# Create a virtual environment
python -m venv .venv

# Activate it (macOS/Linux)
source .venv/bin/activate
# (Windows)
# .venv\Scripts\activate

# Install dependencies (you may need to install per service)
pip install -r backend/requirements.txt
# Repeat for services if they have individual requirements.txt
```

### 3. Environment Variables
You must configure the environment variables for **each** service.
Template files (`.env.example`) have been provided in each service directory.

```bash
# Example: Setting up User Service env
cp services/user_service/.env.example services/user_service/.env
# Now edit services/user_service/.env with your actual credentials
```

You need to do this for:
- `backend/.env`
- `services/user_service/.env`
- `services/assessment_service/.env`
- `services/notification_service/.env`
- `services/ai_service/.env`
- `services/school_service/.env`

> ⚠️ **IMPORTANT**: Never commit actual `.env` files to Git. The `.gitignore` is configured to prevent this.

### 4. Running the Application

A convenience script is provided to start all microservices simultaneously for local development.

```bash
# Ensure the script is executable
chmod +x start_all.sh

# Run all services
./start_all.sh
```

**What the script does:**
1. Verifies the `.venv` exists.
2. Spawns each FastAPI service on its designated port using `uvicorn`.
3. Redirects logs to `logs_<service_name>.log` in the root directory.
4. Performs a health check ping on all ports.

To stop all running services:
```bash
pkill -f uvicorn
```

---

## 🛠️ Tech Stack
- **Framework:** FastAPI (Python)
- **ORM:** SQLAlchemy
- **Database Migrations:** Alembic
- **Databases:** MySQL (Primary Relational), Redis (Caching/Sessions)
- **Server:** Uvicorn

## 📝 Git Workflow
- `main` branch holds the stable, deployable code.
- Create feature branches (`feature/your-feature-name`) for new work.
- `.env` files, `__pycache__`, and `venv` are ignored by default. If adding new secret types, ensure they are added to `.gitignore`.

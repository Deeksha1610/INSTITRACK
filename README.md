# INSTITRACK
### Integrated Institutional Case Tracking, Intelligence and Coordination Platform

**One Institution. Connected Cases. Smarter Decisions.**

INSTITRACK is a centralized web-based platform designed to monitor and track institution-related complaint cases across AICTE bureaus and cells. It supports complaint submission, case review, assignment, progress monitoring, resolution tracking, notifications, and administrative analytics through a unified dashboard.

The platform aims to improve case visibility, coordination, accountability, and decision-making by maintaining a structured record of each case throughout its lifecycle.

> **Project status:** Student project developed for demonstration and academic purposes. It is not an official AICTE platform and does not claim integration with official AICTE systems.

## Problem Statement

**Integrated Dashboard for Monitoring and Tracking Institution-Related Complaint Cases Across AICTE Bureaus/Cells**

## Overview

Institution-related complaints can involve multiple departments, officers, and stages of review. When case information is scattered across different systems or maintained manually, monitoring progress and coordinating responsibilities becomes difficult.

INSTITRACK proposes a centralized dashboard where authorized users can access relevant case information, track progress, manage assignments, monitor deadlines, and review institutional complaint trends.

## Key Features

### 1. Role-Based Access

The platform is designed to support different user roles, with access controlled according to assigned permissions.

- **Complainant:** Submit complaints and view permitted updates on their own cases.
- **Super Admin:** Manage users, roles, institutions, and configurable system settings.
- **Central Monitoring Officer:** Review cases, coordinate assignments, monitor overdue cases, and oversee progress.
- **Bureau Officer:** Handle assigned cases, update progress, request additional information, and submit resolutions.
- **Auditor:** Review authorized case records, action history, and audit information.

### 2. Complaint and Case Management

- Register institution-related complaints through a structured submission process.
- Generate a unique Case ID for tracking.
- Review, accept, return, or reject cases according to configured rules.
- Assign and reassign cases to responsible officers.
- Maintain case status and progress history.
- Record resolution details and support authorized closure or reopening.

### 3. Configurable Case Routing

The system can use configurable rules to recommend a relevant bureau or cell based on complaint details and category.

Cases that cannot be routed confidently can be sent to a review queue. Authorized officers can correct assignments, with changes recorded in the case history.

These rules are configurable project logic and do not represent verified official AICTE routing policies.

### 4. AI-Assisted Related-Case Detection

INSTITRACK can use text-processing techniques to identify potentially similar complaints.

- Convert complaint text into numerical representations using TF-IDF.
- Compare complaint similarity using cosine similarity.
- Highlight potentially related cases for authorized users to review.
- Help identify repeated reports concerning the same or similar issue.

Similarity results are suggestions, not proof that two complaints refer to the same incident.

### 5. Deadline and Escalation Monitoring

The platform is designed to track case deadlines using configurable rules, highlight overdue cases, and support escalation workflows.

### 6. Notifications and Updates

The notification system is intended to inform users about relevant case events, such as assignment changes, requests for information, progress updates, and resolution decisions.

The actual notification mechanism depends on the implementation; see Known Limitations for details.

### 7. Dashboard and Analytics

Authorized users can view relevant case statistics and trends, including:

- Total cases and cases by status.
- Pending, in-progress, and overdue cases.
- Case distribution across bureaus or cells.
- Workload and assignment information.
- Complaint categories and recurring issues.
- Potential hotspots and patterns in historical data.

### 8. Resolution Verification and Audit Trail

The platform supports a structured resolution process, including resolution details and authorized closure decisions. Where implemented, supporting evidence and citizen confirmation can strengthen verification.

Case actions should be recorded with the responsible user, action, and timestamp to support traceability.

### 9. Reports and Data Export

The intended reporting functionality includes exporting authorized case information and summaries to CSV and PDF formats.

## Case Workflow

The proposed workflow follows these stages:

**REPORT → REVIEW → ROUTE → ASSIGN → PROCESS → VERIFY → CLOSE → ANALYZE**

1. **Report:** A complaint is submitted with the available details.
2. **Review:** An authorized officer checks the complaint.
3. **Route:** Configurable rules recommend the relevant bureau or cell.
4. **Assign:** The case is assigned to a responsible officer.
5. **Process:** The officer updates progress or requests additional information.
6. **Verify:** The submitted resolution is reviewed by an authorized user.
7. **Close:** The case is closed after the required approval.
8. **Analyze:** Dashboard metrics and reports help identify recurring patterns.

The backend should validate permitted status transitions and enforce role-based permissions.

## Technology Stack

### Frontend

- **React.js:** Builds the user interface and reusable components.
- **Vite:** Provides frontend development and build tooling.
- **Tailwind CSS:** Supports responsive styling and interface design.
- **React Router:** Manages navigation between pages.
- **Axios:** Communicates with backend APIs.
- **Lucide React:** Provides interface icons.
- **Recharts:** Displays dashboard analytics and charts.

### Backend

- **Python:** Implements application logic and data processing.
- **FastAPI:** Provides REST API endpoints.
- **SQLAlchemy:** Supports database operations through ORM models.
- **Pydantic:** Validates request and response data.
- **JWT:** Supports token-based authentication.
- **Password hashing:** Protects stored user passwords.

### Database

- **SQLite:** Supports local development and demonstration.
- **PostgreSQL:** A possible deployment option for a larger multi-user system, if configured.

### AI and Reporting

- **scikit-learn:** Supports TF-IDF vectorization and cosine-similarity calculations.
- **ReportLab:** Supports PDF generation, where implemented.
- **CSV:** Supports structured data export, where implemented.

## System Architecture

INSTITRACK follows a frontend–backend–database architecture.

**Frontend → REST API → Backend Services → Database**

- **Frontend:** Presents dashboards, forms, case details, and analytics.
- **API layer:** Receives requests and returns structured responses.
- **Backend services:** Handle authentication, authorization, case workflows, routing, notifications, and AI-assisted analysis.
- **Database:** Stores users, cases, assignments, status history, and other configured records.

AI-assisted similarity detection can be invoked by backend services to identify related cases.

## Project Structure

The project is organized into separate frontend and backend applications.

```text
INSTITRACK/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── ai/
│   │   ├── core/
│   │   ├── db/
│   │   ├── tests/
│   │   └── main.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── layouts/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── hooks/
│   │   └── utils/
│   └── package.json
├── .gitignore
└── README.md
```

*The structure above is illustrative. Adjust it to match the actual files in your repository.*

## Getting Started

### Prerequisites

Install the following tools before running the project:

- Python 3.10 or a compatible version required by the backend dependencies.
- Node.js and npm.
- Git.
- Visual Studio Code or another code editor.

### 1. Clone the Repository

```bash
git clone https://github.com/Deeksha1610/INSTITRACK.git
cd INSTITRACK
```


### 2. Set Up the Backend

Open a terminal in the project root and run these commands in PowerShell:

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Configure the local environment variables in `.env` according to the backend configuration.

Start the development server:

```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Backend API:

`http://127.0.0.1:8000`

Interactive API documentation, if enabled:

`http://127.0.0.1:8000/docs`

### 3. Set Up the Frontend

Open a second terminal:

```powershell
cd "F:\sih\INSTITRACK\frontend"
npm install
npm run dev
```

Use the local frontend URL printed by Vite in the terminal, commonly:

`http://localhost:5173`

Ensure the frontend API configuration points to the running backend.

### 4. Verify the Application

- Confirm that the backend starts without errors.
- Open the frontend and verify that it loads.
- Test login and permissions for each configured role.
- Submit a test complaint and confirm that it is stored.
- Test assignment, progress updates, and closure.
- Verify notifications, analytics, exports, and AI-assisted similarity detection individually if they are implemented.

Use fictional test records and verify the application behavior before presenting it as a complete working system.

## Environment Configuration

The backend may require environment variables such as:

- `SECRET_KEY` — used for token signing or related security functions.
- `DATABASE_URL` — specifies the configured database connection.
- `CORS_ORIGINS` — defines permitted frontend origins.
- `SIMILARITY_THRESHOLD` — configures the threshold for suggesting related cases, if supported.

Use `.env.example` to identify the variables expected by the actual application. Keep `.env` out of Git and never publish production secrets.

## Security Considerations

- Enforce role-based permissions on the backend, not only in the frontend.
- Hash passwords before storing them.
- Validate input data and uploaded files.
- Restrict access to complaint details and attachments.
- Protect sensitive configuration through environment variables.
- Record important case actions for traceability.
- Use HTTPS and appropriate production security settings when deployed.

## Known Limitations

The following points should be checked against the current implementation before release:

- Email and SMS delivery may require additional services.
- Real-time notifications may use polling rather than WebSockets.
- Uploaded files may be stored locally rather than in cloud storage.
- Production deployment may require PostgreSQL, database migrations, backups, and stronger concurrency handling.
- AI-generated similarity suggestions may require human review.
- Official AICTE system integration is not claimed.

## Future Enhancements

- WebSocket-based real-time notifications.
- Improved workload-aware assignment recommendations.
- Advanced trend and hotspot analysis.
- Predictive insights using historical case data.
- Secure cloud storage for attachments.
- Production-grade deployment, monitoring, and automated testing.
- Integration with authorized external systems where APIs and permissions are available.

## Expected Impact

INSTITRACK aims to improve institutional complaint monitoring through centralized case visibility, structured workflows, clearer assignment responsibilities, traceable actions, and data-driven reporting.

By bringing relevant case information into one dashboard, the platform can help authorized teams identify pending cases, coordinate work, and recognize recurring complaint patterns.

## Team Information

- **Team Name:** New Waves
- **Project:** INSTITRACK
- **Hackathon:** Smart India Hackathon (SIH)
- **Theme:** Smart automation 
-
- 

## Disclaimer

INSTITRACK is an academic project developed for demonstration and evaluation. It is not an official AICTE product, and its sample records, routing rules, deadlines, and analytics must not be interpreted as official institutional data or policy.



## License

No open-source license has been selected for this project yet.

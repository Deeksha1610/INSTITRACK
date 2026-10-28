"""
Basic backend tests for INSTITRACK authentication and case lifecycle.
Run: pytest app/tests/ -v
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.session import Base, get_db
from app.core.security import get_password_hash
from app.models.user import User, RoleEnum
from app.models.institution import Institution
from app.models.bureau import Bureau
from app.models.case import CaseCategory

# In-memory SQLite for tests
SQLALCHEMY_DATABASE_URL = "sqlite://"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    # Seed minimal data
    bureau = Bureau(code="TEST", name="Test Bureau", description="Test")
    db.add(bureau)
    db.flush()
    inst = Institution(
        institution_id="TEST-INST-001",
        name="Test Institution",
        state="Test State",
        is_active=True,
    )
    db.add(inst)
    admin = User(
        username="testadmin",
        email="admin@test.com",
        full_name="Test Admin",
        hashed_password=get_password_hash("Test@123"),
        role=RoleEnum.SUPER_ADMIN,
    )
    complainant = User(
        username="teststudent",
        email="student@test.com",
        full_name="Test Student",
        hashed_password=get_password_hash("Test@123"),
        role=RoleEnum.COMPLAINANT,
    )
    monitor = User(
        username="testmonitor",
        email="monitor@test.com",
        full_name="Test Monitor",
        hashed_password=get_password_hash("Test@123"),
        role=RoleEnum.CENTRAL_MONITORING,
    )
    officer = User(
        username="testofficer",
        email="officer@test.com",
        full_name="Test Officer",
        hashed_password=get_password_hash("Test@123"),
        role=RoleEnum.BUREAU_OFFICER,
        bureau_id=bureau.id,
    )
    db.add_all([admin, complainant, monitor, officer])
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


def login(username: str, password: str = "Test@123"):
    r = client.post("/api/auth/login", data={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_login_and_me():
    token = login("teststudent")
    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["username"] == "teststudent"
    assert r.json()["role"] == "complainant"


def test_complaint_to_closure_workflow():
    # 1. Complainant submits
    student_token = login("teststudent")
    # Get institution
    # Institutions require auth in list, but public endpoint exists
    r = client.get("/api/institutions/public")
    assert r.status_code == 200
    insts = r.json()
    assert len(insts) >= 1
    inst_id = insts[0]["id"]

    payload = {
        "title": "Test complaint about examination delay for workflow",
        "description": "This is a detailed test description for the automated end-to-end workflow test of INSTITRACK platform. Minimum length required.",
        "category": CaseCategory.ACADEMIC_EXAM.value,
        "institution_id": inst_id,
    }
    r = client.post("/api/cases", json=payload, headers={"Authorization": f"Bearer {student_token}"})
    assert r.status_code == 200, r.text
    case = r.json()
    assert case["status"] == "SUBMITTED"
    assert case["case_id"].startswith("INST-")
    case_db_id = case["id"]

    # 2. Monitor accepts
    monitor_token = login("testmonitor")
    r = client.post(f"/api/cases/{case_db_id}/accept", json={}, headers={"Authorization": f"Bearer {monitor_token}"})
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "ACCEPTED"

    # 3. Monitor assigns
    # Get bureau
    r = client.get("/api/bureaus", headers={"Authorization": f"Bearer {monitor_token}"})
    assert r.status_code == 200
    bureaus = r.json()
    assert len(bureaus) >= 1
    bureau_id = bureaus[0]["id"]

    r = client.get("/api/users/officers", headers={"Authorization": f"Bearer {monitor_token}"})
    officers = r.json()
    officer_id = officers[0]["id"] if officers else None

    assign_payload = {"bureau_id": bureau_id, "officer_id": officer_id, "priority": "MEDIUM", "notes": "Test assignment"}
    r = client.post(f"/api/cases/{case_db_id}/assign", json=assign_payload, headers={"Authorization": f"Bearer {monitor_token}"})
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "ASSIGNED"

    # 4. Officer acknowledges
    officer_token = login("testofficer")
    r = client.post(f"/api/cases/{case_db_id}/acknowledge-assignment", headers={"Authorization": f"Bearer {officer_token}"})
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "IN_PROGRESS"

    # 5. Officer submits resolution
    r = client.post(
        f"/api/cases/{case_db_id}/submit-resolution",
        json={"resolution_summary": "Issue investigated and resolved. Results published on portal."},
        headers={"Authorization": f"Bearer {officer_token}"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "RESOLUTION_SUBMITTED"

    # 6. Monitor approves closure
    r = client.post(
        f"/api/cases/{case_db_id}/approve-closure",
        json={"approve": True, "remarks": "Verified and closed"},
        headers={"Authorization": f"Bearer {monitor_token}"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "CLOSED"

    # 7. Case detail has history
    r = client.get(f"/api/cases/{case_db_id}", headers={"Authorization": f"Bearer {monitor_token}"})
    assert r.status_code == 200
    detail = r.json()
    assert len(detail["history"]) >= 4
    assert detail["status"] == "CLOSED"


def test_unauthorized_access():
    student_token = login("teststudent")
    # Student cannot accept cases
    r = client.post("/api/cases/1/accept", json={}, headers={"Authorization": f"Bearer {student_token}"})
    assert r.status_code in (403, 404)

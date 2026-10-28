"""
Safe, idempotent seed script for INSTITRACK demonstration data.
All data is fictional and labelled for SIH demonstration only.
"""
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.user import User, RoleEnum
from app.models.institution import Institution
from app.models.bureau import Bureau
from app.models.case import (
    Case, CaseStatus, CasePriority, CaseCategory, CaseAssignment,
    CaseHistory, DeadlineRule, CategoryBureauRule, Notification, RelatedCase
)


def seed_if_empty(db: Session):
    if db.query(User).first():
        print("Database already has users — skipping seed (idempotent).")
        return
    print("Seeding INSTITRACK demonstration data...")
    seed_all(db)
    print("Seed complete.")


def seed_all(db: Session):
    # --- Bureaus (fictional demo cells) ---
    bureaus_data = [
        ("ACAD", "Academic Affairs Cell", "Handles academic and examination related complaints (demo)"),
        ("ADMS", "Admissions Cell", "Admission process and related grievances (demo)"),
        ("FACI", "Facilities & Infrastructure Cell", "Campus facilities and infrastructure issues (demo)"),
        ("FEE", "Fee & Finance Cell", "Fee-related complaints and refunds (demo)"),
        ("STAF", "Faculty & Staff Grievance Cell", "Faculty and staff related matters (demo)"),
        ("STU", "Student Welfare Cell", "General student grievances (demo)"),
        ("REG", "Regulatory Compliance Cell", "Regulatory and compliance concerns (demo)"),
    ]
    bureaus = {}
    for code, name, desc in bureaus_data:
        b = Bureau(code=code, name=name, description=desc)
        db.add(b)
        db.flush()
        bureaus[code] = b

    # --- Institutions (fictional) ---
    institutions_data = [
        ("DEMO-INST-001", "Northern Technical Institute", "Engineering College", "Uttar Pradesh", "Lucknow", "Lucknow"),
        ("DEMO-INST-002", "Southern Polytechnic College", "Polytechnic", "Tamil Nadu", "Chennai", "Chennai"),
        ("DEMO-INST-003", "Eastern University of Technology", "University", "West Bengal", "Kolkata", "Kolkata"),
        ("DEMO-INST-004", "Western Institute of Management", "Management Institute", "Maharashtra", "Pune", "Pune"),
        ("DEMO-INST-005", "Central Engineering Academy", "Engineering College", "Madhya Pradesh", "Bhopal", "Bhopal"),
        ("DEMO-INST-006", "Coastal Maritime College", "Specialized College", "Kerala", "Kochi", "Kochi"),
        ("DEMO-INST-007", "Hillside Agricultural Institute", "Agricultural College", "Himachal Pradesh", "Shimla", "Shimla"),
        ("DEMO-INST-008", "Desert Research Polytechnic", "Polytechnic", "Rajasthan", "Jodhpur", "Jodhpur"),
    ]
    institutions = []
    for iid, name, itype, state, district, city in institutions_data:
        inst = Institution(
            institution_id=iid,
            name=name,
            institution_type=itype,
            state=state,
            district=district,
            city=city,
            address=f"Demo Campus, {city}, {state}",
            contact_email=f"contact@{iid.lower().replace('-', '')}.demo",
            registration_ref=f"REG-{iid}",
            is_active=True,
        )
        db.add(inst)
        db.flush()
        institutions.append(inst)

    # --- Users ---
    users_spec = [
        ("admin", "admin@institack.demo", "System Super Admin", RoleEnum.SUPER_ADMIN, None, "Admin@123"),
        ("monitor1", "monitor1@institack.demo", "Priya Sharma (Central Monitor)", RoleEnum.CENTRAL_MONITORING, None, "Monitor@123"),
        ("monitor2", "monitor2@institack.demo", "Rajesh Kumar (Central Monitor)", RoleEnum.CENTRAL_MONITORING, None, "Monitor@123"),
        ("officer_acad", "officer.acad@institack.demo", "Ananya Reddy (Academic Officer)", RoleEnum.BUREAU_OFFICER, "ACAD", "Officer@123"),
        ("officer_adms", "officer.adms@institack.demo", "Vikram Singh (Admissions Officer)", RoleEnum.BUREAU_OFFICER, "ADMS", "Officer@123"),
        ("officer_faci", "officer.faci@institack.demo", "Meera Patel (Facilities Officer)", RoleEnum.BUREAU_OFFICER, "FACI", "Officer@123"),
        ("officer_fee", "officer.fee@institack.demo", "Suresh Nair (Fee Officer)", RoleEnum.BUREAU_OFFICER, "FEE", "Officer@123"),
        ("officer_stu", "officer.stu@institack.demo", "Kavita Joshi (Student Welfare)", RoleEnum.BUREAU_OFFICER, "STU", "Officer@123"),
        ("auditor1", "auditor@institack.demo", "Deepak Verma (Auditor)", RoleEnum.AUDITOR, None, "Auditor@123"),
        ("complainant1", "student1@demo.edu", "Arjun Mehta (Student)", RoleEnum.COMPLAINANT, None, "Student@123"),
        ("complainant2", "parent1@demo.com", "Sunita Gupta (Parent)", RoleEnum.COMPLAINANT, None, "Student@123"),
        ("complainant3", "faculty1@demo.edu", "Dr. Neha Kapoor (Faculty)", RoleEnum.COMPLAINANT, None, "Student@123"),
    ]
    users = {}
    for username, email, full_name, role, bureau_code, password in users_spec:
        u = User(
            username=username,
            email=email,
            full_name=full_name,
            hashed_password=get_password_hash(password),
            role=role,
            bureau_id=bureaus[bureau_code].id if bureau_code else None,
            phone="9999900000",
            is_active=True,
        )
        db.add(u)
        db.flush()
        users[username] = u

    # --- Deadline rules ---
    for cat, days in [
        (CaseCategory.ACADEMIC_EXAM, 21),
        (CaseCategory.ADMISSION, 14),
        (CaseCategory.FEE, 15),
        (CaseCategory.FACILITIES, 30),
        (CaseCategory.STUDENT_GRIEVANCE, 20),
        (None, 30),  # default
    ]:
        db.add(DeadlineRule(name=f"Rule-{cat.value if cat else 'Default'}", category=cat, days_to_resolve=days))

    # --- Category routing rules ---
    routing = [
        (CaseCategory.ACADEMIC_EXAM, "ACAD"),
        (CaseCategory.ADMISSION, "ADMS"),
        (CaseCategory.FACILITIES, "FACI"),
        (CaseCategory.INFRASTRUCTURE, "FACI"),
        (CaseCategory.FEE, "FEE"),
        (CaseCategory.FACULTY_STAFF, "STAF"),
        (CaseCategory.STUDENT_GRIEVANCE, "STU"),
        (CaseCategory.REGULATORY, "REG"),
        (CaseCategory.OTHER, "STU"),
    ]
    for cat, code in routing:
        db.add(CategoryBureauRule(category=cat, bureau_id=bureaus[code].id))

    # --- Sample cases in various stages ---
    now = datetime.now(timezone.utc)
    sample_cases = [
        {
            "case_id": "INST-2026-00001",
            "title": "Delay in semester examination results publication",
            "description": "The final semester examination results for B.Tech Computer Science have not been published even after 45 days from the last examination date. Students are unable to apply for higher studies and jobs. Multiple requests to the examination cell have gone unanswered. This is a demonstration complaint for SIH.",
            "category": CaseCategory.ACADEMIC_EXAM,
            "status": CaseStatus.SUBMITTED,
            "institution": institutions[0],
            "complainant": users["complainant1"],
            "days_ago": 2,
        },
        {
            "case_id": "INST-2026-00002",
            "title": "Excessive and unexplained fee hike for the academic year",
            "description": "The institution has increased tuition fees by 35% without prior notice or detailed breakup of the additional charges. Scholarship students are particularly affected. Requesting transparent fee structure and rollback of unjustified components. Demonstration data only.",
            "category": CaseCategory.FEE,
            "status": CaseStatus.ACCEPTED,
            "institution": institutions[1],
            "complainant": users["complainant2"],
            "days_ago": 5,
        },
        {
            "case_id": "INST-2026-00003",
            "title": "Non-functional laboratory equipment in electronics lab",
            "description": "More than half of the oscilloscopes and signal generators in the Electronics Laboratory have been non-functional for over three months. Practical sessions are severely impacted. Multiple complaints to the department head have not resulted in repairs. SIH demo case.",
            "category": CaseCategory.FACILITIES,
            "status": CaseStatus.ASSIGNED,
            "institution": institutions[0],
            "complainant": users["complainant1"],
            "days_ago": 8,
            "bureau": "FACI",
            "officer": "officer_faci",
        },
        {
            "case_id": "INST-2026-00004",
            "title": "Irregularities in counselling and seat allotment process",
            "description": "During the recent admission counselling, several candidates with higher ranks were not allotted seats while lower-rank candidates were admitted in the same branch. Requesting investigation into the allotment algorithm and transparency in the process. Fictional demonstration complaint.",
            "category": CaseCategory.ADMISSION,
            "status": CaseStatus.IN_PROGRESS,
            "institution": institutions[3],
            "complainant": users["complainant2"],
            "days_ago": 12,
            "bureau": "ADMS",
            "officer": "officer_adms",
        },
        {
            "case_id": "INST-2026-00005",
            "title": "Hostel mess food quality and hygiene concerns",
            "description": "Students residing in Hostel Block C have repeatedly reported poor food quality, insufficient variety, and hygiene issues in the mess kitchen. Pest sightings have also been reported. Requesting immediate inspection and corrective action. Demo case for SIH.",
            "category": CaseCategory.STUDENT_GRIEVANCE,
            "status": CaseStatus.RESOLUTION_SUBMITTED,
            "institution": institutions[2],
            "complainant": users["complainant1"],
            "days_ago": 20,
            "bureau": "STU",
            "officer": "officer_stu",
            "resolution": "Inspection conducted. Kitchen deep-cleaned. New vendor contracted for improved menu. Quality checks scheduled weekly for next quarter.",
        },
        {
            "case_id": "INST-2026-00006",
            "title": "Faculty attendance and cancelled lecture issues",
            "description": "Several core subject lectures in the Mechanical Engineering department have been cancelled without prior notice or makeup classes. Students are concerned about syllabus coverage before examinations. Demonstration complaint only.",
            "category": CaseCategory.FACULTY_STAFF,
            "status": CaseStatus.CLOSED,
            "institution": institutions[4],
            "complainant": users["complainant3"],
            "days_ago": 40,
            "bureau": "STAF",
            "resolution": "Department scheduled makeup classes. Attendance monitoring strengthened. Case closed after verification.",
        },
        {
            "case_id": "INST-2026-00007",
            "title": "Library digital access credentials not working",
            "description": "Newly enrolled students are unable to access digital library resources with the provided credentials. IT support has not resolved the issue for two weeks. Affects research and assignment work. SIH fictional case.",
            "category": CaseCategory.FACILITIES,
            "status": CaseStatus.NEEDS_INFORMATION,
            "institution": institutions[5],
            "complainant": users["complainant1"],
            "days_ago": 6,
            "info_request": "Please provide student enrollment numbers and the exact error message shown when attempting login.",
        },
        {
            "case_id": "INST-2026-00008",
            "title": "Delay in examination results for final year students",
            "description": "Final year B.E. results have been delayed beyond the announced timeline. Students require marksheets for higher education applications and campus placements. Similar to other academic delay complaints. Demonstration data.",
            "category": CaseCategory.ACADEMIC_EXAM,
            "status": CaseStatus.UNDER_REVIEW,
            "institution": institutions[0],
            "complainant": users["complainant3"],
            "days_ago": 3,
        },
    ]

    created_cases = []
    for sc in sample_cases:
        created = now - timedelta(days=sc["days_ago"])
        case = Case(
            case_id=sc["case_id"],
            tracking_ref=f"trk-{sc['case_id'].lower().replace('-', '')}",
            title=sc["title"],
            description=sc["description"],
            category=sc["category"],
            status=sc["status"],
            priority=CasePriority.MEDIUM,
            institution_id=sc["institution"].id,
            complainant_id=sc["complainant"].id,
            created_at=created,
            updated_at=created,
            deadline=created + timedelta(days=30),
            information_request=sc.get("info_request"),
            resolution_summary=sc.get("resolution"),
            closed_at=created + timedelta(days=25) if sc["status"] == CaseStatus.CLOSED else None,
        )
        if sc.get("bureau"):
            case.assigned_bureau_id = bureaus[sc["bureau"]].id
        if sc.get("officer"):
            case.assigned_officer_id = users[sc["officer"]].id
        db.add(case)
        db.flush()
        created_cases.append(case)

        # History
        db.add(CaseHistory(
            case_id=case.id, actor_id=sc["complainant"].id,
            action="CASE_SUBMITTED", to_status=CaseStatus.SUBMITTED.value,
            remarks="Complaint submitted", created_at=created,
        ))
        if sc["status"] != CaseStatus.SUBMITTED:
            db.add(CaseHistory(
                case_id=case.id, actor_id=users["monitor1"].id,
                action="STATUS_UPDATED", from_status=CaseStatus.SUBMITTED.value,
                to_status=sc["status"].value, remarks="Processed by monitoring officer",
                created_at=created + timedelta(days=1),
            ))
        if sc.get("bureau"):
            db.add(CaseAssignment(
                case_id=case.id,
                bureau_id=bureaus[sc["bureau"]].id,
                officer_id=users[sc["officer"]].id if sc.get("officer") else None,
                assigned_by_id=users["monitor1"].id,
                priority=CasePriority.MEDIUM,
                acknowledged=sc["status"] in [CaseStatus.IN_PROGRESS, CaseStatus.RESOLUTION_SUBMITTED, CaseStatus.CLOSED],
                is_current=True,
                created_at=created + timedelta(days=2),
            ))

    # Related case suggestion between 00001 and 00008 (similar academic delay)
    if len(created_cases) >= 8:
        db.add(RelatedCase(
            source_case_id=created_cases[0].id,
            target_case_id=created_cases[7].id,
            similarity_score=0.72,
            confirmed=False,
        ))

    # Sample notifications
    db.add(Notification(
        user_id=users["monitor1"].id,
        title="New Complaint Submitted",
        message=f"Case {created_cases[0].case_id}: {created_cases[0].title}",
        notification_type="new_case",
        case_id=created_cases[0].id,
    ))
    db.add(Notification(
        user_id=users["officer_faci"].id,
        title="New Case Assigned",
        message=f"Case {created_cases[2].case_id} has been assigned to you.",
        notification_type="assignment",
        case_id=created_cases[2].id,
    ))
    db.add(Notification(
        user_id=users["complainant1"].id,
        title="Case Status Updated",
        message=f"Your case {created_cases[2].case_id} is now ASSIGNED.",
        notification_type="status",
        case_id=created_cases[2].id,
    ))

    db.commit()
    print(f"Seeded: {len(bureaus)} bureaus, {len(institutions)} institutions, {len(users)} users, {len(created_cases)} cases")

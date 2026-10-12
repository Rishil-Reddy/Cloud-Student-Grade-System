from firebase_admin import auth
from dotenv import load_dotenv
from auth_middleware import get_db, initialize_firebase
from config import Config
from grade_calculator import get_grade_for_score

load_dotenv()
initialize_firebase()

db = get_db()

def seed_database():
    print("[*] Starting database seed script...")
    
    # 1. System Config: Grade Scale
    print("-> Seeding Grade Scale config...")
    db.collection("system_config").document("grade_scale").set({
        "scale": Config.DEFAULT_GRADE_SCALE
    })
    
    # 2. Semester
    print("-> Seeding Semesters...")
    semesters = [
        {"id": "SEM-2025-SPRING", "name": "Spring 2025", "academic_year": "2024-2025", "is_active": True},
        {"id": "SEM-2024-FALL", "name": "Fall 2024", "academic_year": "2024-2025", "is_active": True}
    ]
    for sem in semesters:
        db.collection("semesters").document(sem["id"]).set(sem)
        
    # 3. Users (1 Admin, 2 Teachers, 5 Students)
    users_to_create = [
        # Admin
        {
            "uid": "admin-001",
            "email": "admin@university.edu",
            "password": "AdminPassword123!",
            "name": "System Administrator",
            "role": "admin"
        },
        # Teachers
        {
            "uid": "teacher-001",
            "email": "dr.smith@university.edu",
            "password": "TeacherPassword123!",
            "name": "Dr. Alan Smith",
            "role": "teacher"
        },
        {
            "uid": "teacher-002",
            "email": "prof.johnson@university.edu",
            "password": "TeacherPassword123!",
            "name": "Prof. Sarah Johnson",
            "role": "teacher"
        },
        # Students
        {
            "uid": "student-101",
            "email": "alice@student.university.edu",
            "password": "StudentPassword123!",
            "name": "Alice Walker",
            "role": "student",
            "student_id": "STU2025001"
        },
        {
            "uid": "student-102",
            "email": "bob@student.university.edu",
            "password": "StudentPassword123!",
            "name": "Bob Miller",
            "role": "student",
            "student_id": "STU2025002"
        },
        {
            "uid": "student-103",
            "email": "charlie@student.university.edu",
            "password": "StudentPassword123!",
            "name": "Charlie Davis",
            "role": "student",
            "student_id": "STU2025003"
        },
        {
            "uid": "student-104",
            "email": "diana@student.university.edu",
            "password": "StudentPassword123!",
            "name": "Diana Evans",
            "role": "student",
            "student_id": "STU2025004"
        },
        {
            "uid": "student-105",
            "email": "ethan@student.university.edu",
            "password": "StudentPassword123!",
            "name": "Ethan Wright",
            "role": "student",
            "student_id": "STU2025005"
        }
    ]
    
    print("-> Creating Auth users & Firestore profiles...")
    for u in users_to_create:
        try:
            # Delete if exists in emulator auth
            try:
                auth.delete_user(u["uid"])
            except Exception:
                pass
                
            # Create user in Auth
            user_rec = auth.create_user(
                uid=u["uid"],
                email=u["email"],
                password=u["password"],
                display_name=u["name"]
            )
            auth.set_custom_user_claims(u["uid"], {"role": u["role"]})
            
            # Create in Firestore
            user_doc = {
                "uid": u["uid"],
                "email": u["email"],
                "name": u["name"],
                "role": u["role"],
                "is_active": True,
                "student_id": u.get("student_id")
            }
            db.collection("users").document(u["uid"]).set(user_doc)
            print(f"   Created user: {u['email']} [{u['role']}]")
        except Exception as e:
            print(f"   Warning creating user {u['email']}: {e}")
            
    # 4. Courses (3 Courses)
    print("-> Seeding Courses & Assigning Teachers...")
    courses = [
        {
            "id": "CS101",
            "code": "CS101",
            "title": "Introduction to Cloud Computing",
            "credits": 4.0,
            "semester_id": "SEM-2025-SPRING",
            "teacher_uids": ["teacher-001"],
            "is_active": True
        },
        {
            "id": "CS102",
            "code": "CS102",
            "title": "Data Structures & Algorithms",
            "credits": 4.0,
            "semester_id": "SEM-2025-SPRING",
            "teacher_uids": ["teacher-002"],
            "is_active": True
        },
        {
            "id": "CS103",
            "code": "CS103",
            "title": "Database Management Systems",
            "credits": 3.0,
            "semester_id": "SEM-2025-SPRING",
            "teacher_uids": ["teacher-001", "teacher-002"],
            "is_active": True
        }
    ]
    for c in courses:
        db.collection("courses").document(c["id"]).set(c)
        
    # 5. Seed Initial Marks for Spring 2025
    print("-> Seeding Initial Marks for Students...")
    sample_scores = [
        # Alice (High achiever)
        ("student-101", "Alice Walker", "STU2025001", "CS101", "CS101", "Introduction to Cloud Computing", 4.0, 94.0, "teacher-001"),
        ("student-101", "Alice Walker", "STU2025001", "CS102", "CS102", "Data Structures & Algorithms", 4.0, 88.5, "teacher-002"),
        ("student-101", "Alice Walker", "STU2025001", "CS103", "CS103", "Database Management Systems", 3.0, 91.0, "teacher-001"),
        
        # Bob (Average)
        ("student-102", "Bob Miller", "STU2025002", "CS101", "CS101", "Introduction to Cloud Computing", 4.0, 74.0, "teacher-001"),
        ("student-102", "Bob Miller", "STU2025002", "CS102", "CS102", "Data Structures & Algorithms", 4.0, 68.0, "teacher-002"),
        ("student-102", "Bob Miller", "STU2025002", "CS103", "CS103", "Database Management Systems", 3.0, 72.0, "teacher-001"),
        
        # Charlie (Needs improvement)
        ("student-103", "Charlie Davis", "STU2025003", "CS101", "CS101", "Introduction to Cloud Computing", 4.0, 55.0, "teacher-001"),
        ("student-103", "Charlie Davis", "STU2025003", "CS102", "CS102", "Data Structures & Algorithms", 4.0, 38.0, "teacher-002"), # Fail
        ("student-103", "Charlie Davis", "STU2025003", "CS103", "CS103", "Database Management Systems", 3.0, 62.0, "teacher-001"),
    ]
    
    for stu_uid, stu_name, stu_id, c_id, c_code, c_title, creds, score, teacher in sample_scores:
        grade_info = get_grade_for_score(score, Config.DEFAULT_GRADE_SCALE)
        mark_id = f"SEM-2025-SPRING_{c_id}_{stu_uid}"
        db.collection("marks").document(mark_id).set({
            "id": mark_id,
            "student_uid": stu_uid,
            "student_id": stu_id,
            "student_name": stu_name,
            "course_id": c_id,
            "course_code": c_code,
            "course_title": c_title,
            "credits": creds,
            "semester_id": "SEM-2025-SPRING",
            "score": score,
            "max_marks": 100.0,
            "percentage": score,
            "grade": grade_info["grade"],
            "grade_points": grade_info["grade_points"],
            "is_pass": grade_info["is_pass"],
            "teacher_uids": ["teacher-001"] if c_id == "CS101" else (["teacher-002"] if c_id == "CS102" else ["teacher-001", "teacher-002"]),
            "entered_by": teacher
        })
        
    print("[+] Database seeding completed successfully!")

if __name__ == '__main__':
    seed_database()

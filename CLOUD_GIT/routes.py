import os
import csv
import io
from flask import Blueprint, request, jsonify, g, send_file
from auth_middleware import require_auth, require_role, get_db
from grade_calculator import get_grade_for_score, calculate_gpa, calculate_class_statistics
from audit_logger import log_marks_audit
from pdf_generator import generate_student_result_pdf
from config import Config
from firebase_admin import auth

api_bp = Blueprint('api', __name__)

def get_grade_scale_config():
    db = get_db()
    try:
        cfg_doc = db.collection("system_config").document("grade_scale").get()
        if cfg_doc.exists:
            return cfg_doc.to_dict().get("scale", Config.DEFAULT_GRADE_SCALE)
    except Exception:
        pass
    return Config.DEFAULT_GRADE_SCALE

# ==========================================
# PUBLIC / AUTH STATUS ROUTES
# ==========================================

@api_bp.route('/config/grade-scale', methods=['GET'])
def get_grade_scale():
    scale = get_grade_scale_config()
    return jsonify({"scale": scale}), 200

@api_bp.route('/auth/me', methods=['GET'])
@require_auth
def get_current_user_profile():
    return jsonify({
        "user": g.user_data
    }), 200

# ==========================================
# ADMIN ROUTES
# ==========================================

@api_bp.route('/admin/users', methods=['GET'])
@require_role(['admin'])
def list_users():
    role_filter = request.args.get('role')
    db = get_db()
    users_ref = db.collection('users')
    
    if role_filter:
        docs = users_ref.where('role', '==', role_filter).stream()
    else:
        docs = users_ref.stream()
        
    users = [doc.to_dict() for doc in docs]
    return jsonify({"users": users}), 200

@api_bp.route('/admin/users', methods=['POST'])
@require_role(['admin'])
def create_user():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', 'Password@123')
    name = data.get('name', '').strip()
    role = data.get('role', 'student').strip().lower()
    student_id = data.get('student_id', '').strip()
    
    if not email or not name or role not in ['admin', 'teacher', 'student']:
        return jsonify({"error": "Invalid input", "message": "Valid email, name, and role are required."}), 400
        
    db = get_db()
    try:
        # Create user in Firebase Auth
        user_record = auth.create_user(
            email=email,
            password=password,
            display_name=name
        )
        uid = user_record.uid
        
        # Set custom claims on user for Firebase Auth / Security Rules
        auth.set_custom_user_claims(uid, {"role": role})
        
        user_doc_data = {
            "uid": uid,
            "email": email,
            "name": name,
            "role": role,
            "is_active": True,
            "student_id": student_id if role == 'student' else None
        }
        db.collection('users').document(uid).set(user_doc_data)
        
        return jsonify({"message": "User created successfully", "user": user_doc_data}), 201
    except Exception as e:
        return jsonify({"error": "User creation failed", "message": str(e)}), 400

@api_bp.route('/admin/users/<uid>', methods=['PUT'])
@require_role(['admin'])
def update_user(uid):
    data = request.get_json() or {}
    db = get_db()
    user_ref = db.collection('users').document(uid)
    doc = user_ref.get()
    
    if not doc.exists:
        return jsonify({"error": "Not Found", "message": "User not found"}), 404
        
    update_data = {}
    if 'name' in data:
        update_data['name'] = data['name']
    if 'is_active' in data:
        update_data['is_active'] = bool(data['is_active'])
    if 'role' in data and data['role'] in ['admin', 'teacher', 'student']:
        update_data['role'] = data['role']
        try:
            auth.set_custom_user_claims(uid, {"role": data['role']})
        except Exception:
            pass
    if 'student_id' in data:
        update_data['student_id'] = data['student_id']
        
    if update_data:
        user_ref.update(update_data)
        
    updated = user_ref.get().to_dict()
    return jsonify({"message": "User updated", "user": updated}), 200

@api_bp.route('/admin/semesters', methods=['GET'])
@require_role(['admin', 'teacher', 'student'])
def list_semesters():
    db = get_db()
    docs = db.collection('semesters').stream()
    semesters = [doc.to_dict() for doc in docs]
    return jsonify({"semesters": semesters}), 200

@api_bp.route('/admin/semesters', methods=['POST'])
@require_role(['admin'])
def create_semester():
    data = request.get_json() or {}
    sem_id = data.get('id', '').strip()
    name = data.get('name', '').strip()
    academic_year = data.get('academic_year', '').strip()
    
    if not sem_id or not name:
        return jsonify({"error": "Invalid input", "message": "Semester ID and Name are required"}), 400
        
    db = get_db()
    sem_data = {
        "id": sem_id,
        "name": name,
        "academic_year": academic_year,
        "is_active": True
    }
    db.collection('semesters').document(sem_id).set(sem_data)
    return jsonify({"message": "Semester created", "semester": sem_data}), 201

@api_bp.route('/admin/courses', methods=['GET'])
@require_role(['admin', 'teacher', 'student'])
def list_courses():
    semester_id = request.args.get('semester_id')
    db = get_db()
    courses_ref = db.collection('courses')
    
    if semester_id:
        docs = courses_ref.where('semester_id', '==', semester_id).stream()
    else:
        docs = courses_ref.stream()
        
    courses = [doc.to_dict() for doc in docs]
    return jsonify({"courses": courses}), 200

@api_bp.route('/admin/courses', methods=['POST'])
@require_role(['admin'])
def create_course():
    data = request.get_json() or {}
    course_id = data.get('id', '').strip().upper()
    code = data.get('code', course_id).strip().upper()
    title = data.get('title', '').strip()
    credits = float(data.get('credits', 3.0))
    semester_id = data.get('semester_id', '').strip()
    teacher_uids = data.get('teacher_uids', [])
    
    if not course_id or not title or not semester_id:
        return jsonify({"error": "Invalid input", "message": "Course ID, title, and semester_id are required"}), 400
        
    db = get_db()
    course_data = {
        "id": course_id,
        "code": code,
        "title": title,
        "credits": credits,
        "semester_id": semester_id,
        "teacher_uids": teacher_uids,
        "is_active": True
    }
    db.collection('courses').document(course_id).set(course_data)
    return jsonify({"message": "Course created", "course": course_data}), 201

@api_bp.route('/admin/courses/<course_id>/assign-teacher', methods=['PUT'])
@require_role(['admin'])
def assign_teacher_to_course(course_id):
    data = request.get_json() or {}
    teacher_uids = data.get('teacher_uids', [])
    if not isinstance(teacher_uids, list):
        return jsonify({"error": "Invalid input", "message": "teacher_uids must be a list of UIDs"}), 400
        
    db = get_db()
    course_ref = db.collection('courses').document(course_id)
    doc = course_ref.get()
    if not doc.exists:
        return jsonify({"error": "Not Found", "message": "Course not found"}), 404
        
    course_ref.update({"teacher_uids": teacher_uids})
    return jsonify({"message": "Teacher assignments updated", "course": course_ref.get().to_dict()}), 200

@api_bp.route('/admin/audit-logs', methods=['GET'])
@require_role(['admin'])
def get_audit_logs():
    course_id = request.args.get('course_id')
    student_uid = request.args.get('student_uid')
    limit = int(request.args.get('limit', 100))
    
    db = get_db()
    logs_ref = db.collection('audit_logs')
    
    query = logs_ref
    if course_id:
        query = query.where('course_id', '==', course_id)
    if student_uid:
        query = query.where('student_uid', '==', student_uid)
        
    docs = query.limit(limit).stream()
    logs = [d.to_dict() for d in docs]
    # Sort descending by timestamp in memory
    logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    return jsonify({"audit_logs": logs}), 200

# ==========================================
# TEACHER ROUTES
# ==========================================

@api_bp.route('/teacher/courses', methods=['GET'])
@require_role(['teacher', 'admin'])
def get_teacher_courses():
    db = get_db()
    if g.role == 'admin':
        # Admin can view all courses
        docs = db.collection('courses').stream()
    else:
        # Teacher only views assigned courses
        docs = db.collection('courses').where('teacher_uids', 'array_contains', g.uid).stream()
        
    courses = [doc.to_dict() for doc in docs]
    return jsonify({"courses": courses}), 200

@api_bp.route('/teacher/students', methods=['GET'])
@require_role(['teacher', 'admin'])
def get_teacher_students():
    db = get_db()
    docs = db.collection('users').where('role', '==', 'student').stream()
    students = [
        {
            "uid": d.to_dict().get("uid"),
            "student_id": d.to_dict().get("student_id"),
            "name": d.to_dict().get("name"),
            "email": d.to_dict().get("email")
        }
        for d in docs if d.to_dict().get('is_active', True)
    ]
    return jsonify({"students": students}), 200

@api_bp.route('/teacher/courses/<course_id>/marks', methods=['GET'])
@require_role(['teacher', 'admin'])
def get_course_marks(course_id):
    semester_id = request.args.get('semester_id')
    db = get_db()
    
    # Check if teacher is assigned to this course (if not admin)
    if g.role != 'admin':
        course_doc = db.collection('courses').document(course_id).get()
        if not course_doc.exists or g.uid not in course_doc.to_dict().get('teacher_uids', []):
            return jsonify({"error": "Forbidden", "message": "You are not assigned to teach this course"}), 403
            
    query = db.collection('marks').where('course_id', '==', course_id)
    if semester_id:
        query = query.where('semester_id', '==', semester_id)
        
    marks_docs = query.stream()
    marks = [m.to_dict() for m in marks_docs]
    return jsonify({"marks": marks}), 200

@api_bp.route('/teacher/marks', methods=['POST'])
@require_role(['teacher', 'admin'])
def enter_or_update_marks():
    data = request.get_json() or {}
    student_uid = data.get('student_uid', '').strip()
    course_id = data.get('course_id', '').strip().upper()
    semester_id = data.get('semester_id', '').strip()
    score_val = data.get('score')
    
    if not student_uid or not course_id or not semester_id or score_val is None:
        return jsonify({"error": "Invalid input", "message": "student_uid, course_id, semester_id, and score are required"}), 400
        
    try:
        score = float(score_val)
        if score < 0 or score > 100:
            return jsonify({"error": "Validation Error", "message": "Score must be between 0 and 100"}), 400
    except ValueError:
        return jsonify({"error": "Validation Error", "message": "Score must be a valid number"}), 400
        
    db = get_db()
    
    # Validate Course & Teacher Assignment
    course_doc = db.collection('courses').document(course_id).get()
    if not course_doc.exists:
        return jsonify({"error": "Not Found", "message": "Course not found"}), 404
        
    course_data = course_doc.to_dict()
    if g.role != 'admin' and g.uid not in course_data.get('teacher_uids', []):
        return jsonify({"error": "Forbidden", "message": "You are not assigned to this course"}), 403
        
    # Validate Student exists
    student_doc = db.collection('users').document(student_uid).get()
    if not student_doc.exists or student_doc.to_dict().get('role') != 'student':
        return jsonify({"error": "Not Found", "message": "Student not found"}), 404
    student_data = student_doc.to_dict()
    
    # Compute Grade & Grade Points from Scale
    grade_scale = get_grade_scale_config()
    grade_info = get_grade_for_score(score, grade_scale)
    
    # Deterministic Mark Document ID
    mark_id = f"{semester_id}_{course_id}_{student_uid}"
    mark_ref = db.collection('marks').document(mark_id)
    existing_doc = mark_ref.get()
    
    old_value = existing_doc.to_dict() if existing_doc.exists else None
    action_type = "UPDATE_MARKS" if existing_doc.exists else "CREATE_MARKS"
    
    mark_data = {
        "id": mark_id,
        "student_uid": student_uid,
        "student_id": student_data.get("student_id", student_uid),
        "student_name": student_data.get("name", "Student"),
        "course_id": course_id,
        "course_code": course_data.get("code", course_id),
        "course_title": course_data.get("title", ""),
        "credits": float(course_data.get("credits", 3.0)),
        "semester_id": semester_id,
        "score": score,
        "max_marks": 100.0,
        "percentage": score,
        "grade": grade_info["grade"],
        "grade_points": grade_info["grade_points"],
        "is_pass": grade_info["is_pass"],
        "teacher_uids": course_data.get("teacher_uids", []),
        "entered_by": g.uid
    }
    
    mark_ref.set(mark_data)
    
    # Write Audit Log
    log_marks_audit(
        db=db,
        actor_uid=g.uid,
        actor_email=g.user_data.get("email", ""),
        actor_role=g.role,
        action=action_type,
        course_id=course_id,
        student_uid=student_uid,
        old_value=old_value,
        new_value=mark_data,
        ip_address=request.remote_addr
    )
    
    return jsonify({"message": "Marks saved successfully", "mark": mark_data}), 200

@api_bp.route('/teacher/marks/bulk-upload', methods=['POST'])
@require_role(['teacher', 'admin'])
def bulk_upload_marks():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded", "message": "CSV file is required"}), 400
        
    file = request.files['file']
    course_id = request.form.get('course_id', '').strip().upper()
    semester_id = request.form.get('semester_id', '').strip()
    
    if not course_id or not semester_id:
        return jsonify({"error": "Missing parameters", "message": "course_id and semester_id are required"}), 400
        
    if not file.filename.endswith('.csv'):
        return jsonify({"error": "Invalid file type", "message": "Only .csv files are supported"}), 400
        
    db = get_db()
    
    # Verify course & teacher assignment
    course_doc = db.collection('courses').document(course_id).get()
    if not course_doc.exists:
        return jsonify({"error": "Not Found", "message": "Course not found"}), 404
        
    course_data = course_doc.to_dict()
    if g.role != 'admin' and g.uid not in course_data.get('teacher_uids', []):
        return jsonify({"error": "Forbidden", "message": "You are not assigned to teach this course"}), 403
        
    # Read & parse CSV content
    try:
        content = file.stream.read().decode('utf-8-sig')
        stream = io.StringIO(content)
        reader = csv.DictReader(stream)
    except Exception as e:
        return jsonify({"error": "CSV Parse Error", "message": f"Could not read CSV: {str(e)}"}), 400
        
    # Build student lookup maps
    students_query = db.collection('users').where('role', '==', 'student').stream()
    students_by_id = {}
    students_by_email = {}
    students_by_uid = {}
    for s in students_query:
        s_data = s.to_dict()
        if s_data.get('student_id'):
            students_by_id[s_data['student_id'].strip().lower()] = s_data
        if s_data.get('email'):
            students_by_email[s_data['email'].strip().lower()] = s_data
        students_by_uid[s_data['uid']] = s_data
        
    grade_scale = get_grade_scale_config()
    
    processed_count = 0
    errors = []
    success_entries = []
    
    row_index = 1
    for row in reader:
        row_index += 1
        if row_index > 501: # Maximum 500 records safety limit
            errors.append({"row": row_index, "error": "Maximum 500 rows limit exceeded."})
            break
            
        student_identifier = row.get('student_id') or row.get('email') or row.get('student_uid') or row.get('Student ID')
        score_str = row.get('score') or row.get('marks') or row.get('Marks') or row.get('Score')
        
        if not student_identifier or score_str is None:
            errors.append({"row": row_index, "error": "Missing student identifier or score column."})
            continue
            
        try:
            score = float(str(score_str).strip())
            if score < 0 or score > 100:
                errors.append({"row": row_index, "identifier": student_identifier, "error": f"Score {score} is out of bounds (0-100)."})
                continue
        except ValueError:
            errors.append({"row": row_index, "identifier": student_identifier, "error": f"Invalid score value '{score_str}'."})
            continue
            
        # Match student
        ident_clean = str(student_identifier).strip().lower()
        matched_student = students_by_id.get(ident_clean) or students_by_email.get(ident_clean) or students_by_uid.get(str(student_identifier).strip())
        
        if not matched_student:
            errors.append({"row": row_index, "identifier": student_identifier, "error": f"Student '{student_identifier}' not found in registered students."})
            continue
            
        student_uid = matched_student['uid']
        grade_info = get_grade_for_score(score, grade_scale)
        mark_id = f"{semester_id}_{course_id}_{student_uid}"
        
        mark_ref = db.collection('marks').document(mark_id)
        existing_doc = mark_ref.get()
        old_value = existing_doc.to_dict() if existing_doc.exists else None
        action_type = "BULK_UPDATE_MARKS" if existing_doc.exists else "BULK_CREATE_MARKS"
        
        mark_data = {
            "id": mark_id,
            "student_uid": student_uid,
            "student_id": matched_student.get("student_id", student_uid),
            "student_name": matched_student.get("name", "Student"),
            "course_id": course_id,
            "course_code": course_data.get("code", course_id),
            "course_title": course_data.get("title", ""),
            "credits": float(course_data.get("credits", 3.0)),
            "semester_id": semester_id,
            "score": score,
            "max_marks": 100.0,
            "percentage": score,
            "grade": grade_info["grade"],
            "grade_points": grade_info["grade_points"],
            "is_pass": grade_info["is_pass"],
            "teacher_uids": course_data.get("teacher_uids", []),
            "entered_by": g.uid
        }
        
        mark_ref.set(mark_data)
        
        log_marks_audit(
            db=db,
            actor_uid=g.uid,
            actor_email=g.user_data.get("email", ""),
            actor_role=g.role,
            action=action_type,
            course_id=course_id,
            student_uid=student_uid,
            old_value=old_value,
            new_value=mark_data,
            ip_address=request.remote_addr
        )
        
        processed_count += 1
        success_entries.append({"student_id": matched_student.get("student_id"), "student_name": matched_student.get("name"), "score": score, "grade": grade_info["grade"]})
        
    return jsonify({
        "message": f"Bulk upload completed: {processed_count} saved, {len(errors)} errors.",
        "processed_count": processed_count,
        "error_count": len(errors),
        "errors": errors,
        "success_entries": success_entries
    }), 200

@api_bp.route('/reports/class-summary', methods=['GET'])
@require_role(['teacher', 'admin'])
def get_class_summary_report():
    course_id = request.args.get('course_id', '').strip().upper()
    semester_id = request.args.get('semester_id', '').strip()
    
    if not course_id:
        return jsonify({"error": "Missing parameter", "message": "course_id is required"}), 400
        
    db = get_db()
    course_doc = db.collection('courses').document(course_id).get()
    if not course_doc.exists:
        return jsonify({"error": "Not Found", "message": "Course not found"}), 404
        
    course_data = course_doc.to_dict()
    if g.role != 'admin' and g.uid not in course_data.get('teacher_uids', []):
        return jsonify({"error": "Forbidden", "message": "You are not assigned to this course"}), 403
        
    query = db.collection('marks').where('course_id', '==', course_id)
    if semester_id:
        query = query.where('semester_id', '==', semester_id)
        
    marks_list = [d.to_dict() for d in query.stream()]
    stats = calculate_class_statistics(marks_list)
    
    return jsonify({
        "course": course_data,
        "semester_id": semester_id,
        "statistics": stats
    }), 200

# ==========================================
# STUDENT ROUTES (STRICT ACCESS ISOLATION)
# ==========================================

@api_bp.route('/student/results', methods=['GET'])
@require_role(['student', 'admin'])
def get_student_results():
    # If student, strictly force auth UID (never allow query param spoofing)
    target_student_uid = g.uid
    if g.role == 'admin' and request.args.get('student_uid'):
        target_student_uid = request.args.get('student_uid')
        
    semester_id = request.args.get('semester_id')
    db = get_db()
    
    query = db.collection('marks').where('student_uid', '==', target_student_uid)
    if semester_id:
        query = query.where('semester_id', '==', semester_id)
        
    marks = [d.to_dict() for d in query.stream()]
    gpa_data = calculate_gpa(marks)
    
    # Calculate cumulative CGPA across all semesters for this student
    all_marks = [d.to_dict() for d in db.collection('marks').where('student_uid', '==', target_student_uid).stream()]
    cgpa_data = calculate_gpa(all_marks)
    
    return jsonify({
        "student_uid": target_student_uid,
        "semester_id": semester_id,
        "marks": marks,
        "semester_summary": gpa_data,
        "cumulative_summary": {
            "total_credits": cgpa_data["total_credits"],
            "earned_credits": cgpa_data["earned_credits"],
            "cgpa": cgpa_data["gpa"]
        }
    }), 200

@api_bp.route('/student/results/export-pdf', methods=['GET'])
@require_role(['student', 'admin'])
def export_student_result_pdf():
    target_student_uid = g.uid
    if g.role == 'admin' and request.args.get('student_uid'):
        target_student_uid = request.args.get('student_uid')
        
    semester_id = request.args.get('semester_id', '').strip()
    db = get_db()
    
    student_doc = db.collection('users').document(target_student_uid).get()
    if not student_doc.exists:
        return jsonify({"error": "Not Found", "message": "Student record not found"}), 404
    student_data = student_doc.to_dict()
    
    semester_data = {"name": semester_id or "All Semesters", "academic_year": ""}
    if semester_id:
        sem_doc = db.collection('semesters').document(semester_id).get()
        if sem_doc.exists:
            semester_data = sem_doc.to_dict()
            
    query = db.collection('marks').where('student_uid', '==', target_student_uid)
    if semester_id:
        query = query.where('semester_id', '==', semester_id)
        
    marks = [d.to_dict() for d in query.stream()]
    gpa_data = calculate_gpa(marks)
    
    pdf_buffer = generate_student_result_pdf(student_data, semester_data, marks, gpa_data)
    
    filename = f"Result_{student_data.get('student_id', target_student_uid)}_{semester_id or 'All'}.pdf"
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=filename,
        mimetype='application/pdf'
    )

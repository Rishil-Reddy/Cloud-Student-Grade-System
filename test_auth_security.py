import pytest
from unittest.mock import MagicMock, patch
from app import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_unauthenticated_request_rejected(client):
    # Calling protected endpoint without token must return 401
    resp = client.get('/api/admin/users')
    assert resp.status_code == 401
    assert "Unauthorized" in resp.get_json()["error"]

@patch('auth_middleware.auth.verify_id_token')
@patch('auth_middleware.get_db')
def test_student_blocked_from_admin_route(mock_get_db, mock_verify, client):
    # Student token attempting to access admin route
    mock_verify.return_value = {"uid": "student-101", "email": "alice@student.university.edu", "role": "student"}
    
    mock_doc = MagicMock()
    mock_doc.exists = True
    mock_doc.to_dict.return_value = {"uid": "student-101", "role": "student", "is_active": True}
    
    mock_db = MagicMock()
    mock_db.collection.return_value.document.return_value.get.return_value = mock_doc
    mock_get_db.return_value = mock_db
    
    resp = client.get('/api/admin/users', headers={'Authorization': 'Bearer fake-student-token'})
    assert resp.status_code == 403
    assert "Insufficient permissions" in resp.get_json()["message"]

@patch('auth_middleware.auth.verify_id_token')
@patch('routes.get_db')
@patch('auth_middleware.get_db')
def test_teacher_blocked_from_unassigned_course(mock_auth_get_db, mock_routes_get_db, mock_verify, client):
    # Teacher 002 trying to view marks for CS101 (only assigned to Teacher 001)
    mock_verify.return_value = {"uid": "teacher-002", "email": "prof.johnson@university.edu", "role": "teacher"}
    
    mock_user_doc = MagicMock()
    mock_user_doc.exists = True
    mock_user_doc.to_dict.return_value = {"uid": "teacher-002", "role": "teacher", "is_active": True}
    
    mock_course_doc = MagicMock()
    mock_course_doc.exists = True
    mock_course_doc.to_dict.return_value = {"id": "CS101", "teacher_uids": ["teacher-001"]} # teacher-002 not in list
    
    mock_db = MagicMock()
    def collection_side_effect(name):
        mock_coll = MagicMock()
        if name == "users":
            mock_coll.document.return_value.get.return_value = mock_user_doc
        elif name == "courses":
            mock_coll.document.return_value.get.return_value = mock_course_doc
        return mock_coll
        
    mock_db.collection.side_effect = collection_side_effect
    mock_auth_get_db.return_value = mock_db
    mock_routes_get_db.return_value = mock_db
    
    resp = client.get('/api/teacher/courses/CS101/marks', headers={'Authorization': 'Bearer fake-teacher-token'})
    assert resp.status_code == 403
    assert "You are not assigned" in resp.get_json()["message"]

@patch('auth_middleware.auth.verify_id_token')
@patch('routes.get_db')
@patch('auth_middleware.get_db')
def test_student_cannot_access_other_student_data_via_query(mock_auth_get_db, mock_routes_get_db, mock_verify, client):
    # Student 101 requests /api/student/results?student_uid=student-102
    mock_verify.return_value = {"uid": "student-101", "email": "alice@student.university.edu", "role": "student"}
    
    mock_user_doc = MagicMock()
    mock_user_doc.exists = True
    mock_user_doc.to_dict.return_value = {"uid": "student-101", "role": "student", "is_active": True}
    
    mock_db = MagicMock()
    def collection_side_effect(name):
        mock_coll = MagicMock()
        if name == "users":
            mock_coll.document.return_value.get.return_value = mock_user_doc
        elif name == "marks":
            mock_query = MagicMock()
            mock_query.where.return_value = mock_query
            mock_query.stream.return_value = []
            mock_coll.where.return_value = mock_query
        return mock_coll

    mock_db.collection.side_effect = collection_side_effect
    mock_auth_get_db.return_value = mock_db
    mock_routes_get_db.return_value = mock_db
    
    resp = client.get('/api/student/results?student_uid=student-102', headers={'Authorization': 'Bearer fake-student-token'})
    assert resp.status_code == 200
    data = resp.get_json()
    # Server MUST have forced student_uid to be 'student-101'
    assert data["student_uid"] == "student-101"

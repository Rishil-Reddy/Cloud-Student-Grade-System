import pytest
from grade_calculator import get_grade_for_score, calculate_gpa, calculate_class_statistics
from config import Config

def test_grade_calculation_boundaries():
    scale = Config.DEFAULT_GRADE_SCALE
    
    # 95% -> O, 10.0, Pass
    res = get_grade_for_score(95, scale)
    assert res["grade"] == "O"
    assert res["grade_points"] == 10.0
    assert res["is_pass"] is True
    
    # 85% -> A+, 9.0, Pass
    res = get_grade_for_score(85, scale)
    assert res["grade"] == "A+"
    assert res["grade_points"] == 9.0
    assert res["is_pass"] is True
    
    # 45% -> C, 5.0, Pass
    res = get_grade_for_score(45, scale)
    assert res["grade"] == "C"
    assert res["grade_points"] == 5.0
    assert res["is_pass"] is True
    
    # 35% -> F, 0.0, Fail
    res = get_grade_for_score(35, scale)
    assert res["grade"] == "F"
    assert res["grade_points"] == 0.0
    assert res["is_pass"] is False

def test_gpa_calculation():
    # 3 subjects: 4 credits (O/10.0), 4 credits (A+/9.0), 3 credits (A/8.0)
    # Weighted sum: (10*4) + (9*4) + (8*3) = 40 + 36 + 24 = 100
    # Total credits: 4 + 4 + 3 = 11
    # Expected GPA: 100 / 11 = 9.09
    marks = [
        {"credits": 4.0, "grade_points": 10.0, "is_pass": True},
        {"credits": 4.0, "grade_points": 9.0, "is_pass": True},
        {"credits": 3.0, "grade_points": 8.0, "is_pass": True}
    ]
    summary = calculate_gpa(marks)
    assert summary["total_credits"] == 11.0
    assert summary["earned_credits"] == 11.0
    assert summary["gpa"] == 9.09
    assert summary["all_passed"] is True

def test_gpa_with_backlog_fail():
    marks = [
        {"credits": 4.0, "grade_points": 10.0, "is_pass": True},
        {"credits": 4.0, "grade_points": 0.0, "is_pass": False}, # Failed
    ]
    summary = calculate_gpa(marks)
    assert summary["total_credits"] == 8.0
    assert summary["earned_credits"] == 4.0
    assert summary["gpa"] == 5.0
    assert summary["all_passed"] is False

def test_class_statistics():
    marks_list = [
        {"score": 90, "grade": "O", "is_pass": True},
        {"score": 80, "grade": "A+", "is_pass": True},
        {"score": 70, "grade": "A", "is_pass": True},
        {"score": 30, "grade": "F", "is_pass": False}
    ]
    stats = calculate_class_statistics(marks_list)
    assert stats["count"] == 4
    assert stats["highest"] == 90
    assert stats["lowest"] == 30
    assert stats["average"] == 67.5
    assert stats["pass_count"] == 3
    assert stats["fail_count"] == 1
    assert stats["pass_percentage"] == 75.0

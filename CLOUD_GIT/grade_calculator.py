from typing import List, Dict, Any, Tuple

def get_grade_for_score(score: float, grade_scale: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Finds the matching grade record from the grade scale for a given score (0-100).
    """
    score = float(score)
    for entry in grade_scale:
        min_s = float(entry["min_score"])
        max_s = float(entry["max_score"])
        if min_s <= score <= max_s:
            return {
                "grade": entry["grade"],
                "grade_points": float(entry["grade_points"]),
                "is_pass": bool(entry["is_pass"])
            }
            
    # Fallback to failing grade if no band matches
    return {
        "grade": "F",
        "grade_points": 0.0,
        "is_pass": False
    }

def calculate_gpa(marks_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculates GPA based on list of marks records with credits and grade_points.
    GPA = Sum(grade_points * credits) / Sum(credits)
    """
    if not marks_records:
        return {
            "total_credits": 0,
            "earned_credits": 0,
            "gpa": 0.0,
            "all_passed": True
        }
        
    total_credits = 0.0
    weighted_points = 0.0
    earned_credits = 0.0
    all_passed = True
    
    for item in marks_records:
        credits = float(item.get("credits", 3))
        gp = float(item.get("grade_points", 0.0))
        is_pass = bool(item.get("is_pass", False))
        
        total_credits += credits
        weighted_points += (gp * credits)
        if is_pass:
            earned_credits += credits
        else:
            all_passed = False
            
    gpa = round(weighted_points / total_credits, 2) if total_credits > 0 else 0.0
    
    return {
        "total_credits": total_credits,
        "earned_credits": earned_credits,
        "gpa": gpa,
        "all_passed": all_passed
    }

def calculate_class_statistics(marks_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Computes class statistical summary: average, highest, lowest, pass percentage, and grade distribution.
    """
    if not marks_list:
        return {
            "count": 0,
            "average": 0.0,
            "highest": 0.0,
            "lowest": 0.0,
            "pass_count": 0,
            "fail_count": 0,
            "pass_percentage": 0.0,
            "grade_distribution": {}
        }
        
    scores = [float(m["score"]) for m in marks_list]
    pass_count = sum(1 for m in marks_list if m.get("is_pass", False))
    fail_count = len(marks_list) - pass_count
    
    grade_dist = {}
    for m in marks_list:
        g = m.get("grade", "Unknown")
        grade_dist[g] = grade_dist.get(g, 0) + 1
        
    return {
        "count": len(marks_list),
        "average": round(sum(scores) / len(scores), 2),
        "highest": max(scores),
        "lowest": min(scores),
        "pass_count": pass_count,
        "fail_count": fail_count,
        "pass_percentage": round((pass_count / len(marks_list)) * 100, 2),
        "grade_distribution": grade_dist
    }

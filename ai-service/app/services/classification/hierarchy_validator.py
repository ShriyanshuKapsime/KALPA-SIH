from typing import Dict, Any, Tuple


def validate_nic_hierarchy(nic_record: Dict[str, Any]) -> Tuple[bool, float, str]:
    """
    Validates internal structural consistency of an official NIC record:
    Section (1-letter) -> Division (2-digit) -> Group (3-digit) -> Class (4-digit) -> Subclass/Activity (5-digit)
    
    Returns:
      (is_valid: bool, consistency_score: float, reason: str)
    """
    if not nic_record:
        return False, 0.0, "Empty NIC record"

    try:
        activity_code = str(nic_record.get("activity", {}).get("code", "")).strip()
        subclass_code = str(nic_record.get("subclass", {}).get("code", "")).strip()
        class_code = str(nic_record.get("class", {}).get("code", "")).strip()
        group_code = str(nic_record.get("group", {}).get("code", "")).strip()
        div_code = str(nic_record.get("division", {}).get("code", "")).strip()
        sec_code = str(nic_record.get("section", {}).get("code", "")).strip()

        if not activity_code or len(activity_code) < 2:
            return False, 0.0, f"Invalid activity code: {activity_code}"

        # 1. Check Subclass prefix
        if subclass_code and not activity_code.startswith(subclass_code[:4]):
            return False, 0.4, f"Activity {activity_code} does not align with subclass {subclass_code}"

        # 2. Check Class prefix (4-digit)
        if class_code and not activity_code.startswith(class_code):
            return False, 0.5, f"Activity {activity_code} does not start with class {class_code}"

        # 3. Check Group prefix (3-digit)
        if group_code and not activity_code.startswith(group_code):
            return False, 0.6, f"Activity {activity_code} does not start with group {group_code}"

        # 4. Check Division prefix (2-digit)
        if div_code and not activity_code.startswith(div_code):
            return False, 0.7, f"Activity {activity_code} does not start with division {div_code}"

        # 5. Check Section existence
        if not sec_code or len(sec_code) != 1 or not sec_code.isalpha():
            return False, 0.8, f"Invalid section code: {sec_code}"

        return True, 1.0, "NIC-2008 full hierarchy structure validated successfully"

    except Exception as e:
        return False, 0.0, f"Hierarchy validation error: {e}"

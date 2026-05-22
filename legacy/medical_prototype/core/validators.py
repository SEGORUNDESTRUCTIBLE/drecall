# =====================================================
# VALIDATORS
# =====================================================

from core.schemas import *

# =====================================================
# VALIDATE REQUIRED KEYS
# =====================================================

def validate_required_keys(data):

    missing = []

    for key in REQUIRED_KEYS:

        if key not in data:

            missing.append(key)

    return missing

# =====================================================
# VALIDATE CRITICAL KEYS
# =====================================================

def validate_critical_keys(data):

    missing = []

    for key in CRITICAL_KEYS:

        if key not in data:

            missing.append(key)

    return missing

# =====================================================
# VALIDATE EMPTY FIELDS
# =====================================================

def validate_empty_fields(data):

    empty = []

    for key in REJECT_IF_EMPTY:

        if key not in data:

            continue

        value = data[key]

        if value is None:

            empty.append(key)

        elif str(value).strip() == "":

            empty.append(key)

    return empty

# =====================================================
# VALIDATE TAGS
# =====================================================

def validate_tags(tags):

    if not isinstance(tags, list):

        return []

    valid = []

    for tag in tags:

        if tag in VALID_TAGS:

            valid.append(tag)

    return valid

# =====================================================
# SAFE TEXT
# =====================================================

def validate_text(key, text):

    if text is None:

        return ""

    text = str(text)

    limit = MAX_TEXT_LENGTHS.get(key, 1000)

    return text[:limit]

# =====================================================
# VALIDATE SUBJECT
# =====================================================

def validate_subject(subject):

    return subject in VALID_SUBJECTS

# =====================================================
# VALIDATE SYSTEM
# =====================================================

def validate_system(system):

    return system in VALID_SYSTEMS

# =====================================================
# VALIDATE ERROR TYPE
# =====================================================

def validate_error_type(error_type):

    return error_type in VALID_ERROR_TYPES

# =====================================================
# VALIDATE PATTERN TYPE
# =====================================================

def validate_pattern_type(pattern_type):

    return pattern_type in VALID_PATTERN_TYPES

# =====================================================
# VALIDATE JSON STRUCTURE
# =====================================================

def validate_json(data):

    if not isinstance(data, dict):

        return False

    return True

# =====================================================
# FULL VALIDATION PIPELINE
# =====================================================

def full_validation(data):

    report = {

        "valid": True,

        "missing_required": [],

        "missing_critical": [],

        "empty_critical": [],

        "invalid_subject": False,

        "invalid_system": False,

        "invalid_error_type": False,

        "invalid_pattern_type": False
    }

    # =================================================
    # JSON CHECK
    # =================================================

    if not validate_json(data):

        report["valid"] = False

        return report

    # =================================================
    # REQUIRED KEYS
    # =================================================

    report["missing_required"] = (
        validate_required_keys(data)
    )

    # =================================================
    # CRITICAL KEYS
    # =================================================

    report["missing_critical"] = (
        validate_critical_keys(data)
    )

    # =================================================
    # EMPTY FIELDS
    # =================================================

    report["empty_critical"] = (
        validate_empty_fields(data)
    )

    # =================================================
    # SUBJECT
    # =================================================

    if "subject" in data:

        if not validate_subject(data["subject"]):

            report["invalid_subject"] = True

    # =================================================
    # SYSTEM
    # =================================================

    if "system" in data:

        if not validate_system(data["system"]):

            report["invalid_system"] = True

    # =================================================
    # ERROR TYPE
    # =================================================

    if "error_type" in data:

        if not validate_error_type(
            data["error_type"]
        ):

            report["invalid_error_type"] = True

    # =================================================
    # PATTERN TYPE
    # =================================================

    if "pattern_type" in data:

        if not validate_pattern_type(
            data["pattern_type"]
        ):

            report["invalid_pattern_type"] = True

    # =================================================
    # FINAL VALIDITY
    # =================================================

    critical_failure = (

        len(report["missing_critical"]) > 0

        or

        len(report["empty_critical"]) > 0
    )

    high_failure = (

        report["invalid_subject"]

        or

        report["invalid_system"]

        or

        report["invalid_error_type"]

        or

        report["invalid_pattern_type"]
    )

    if critical_failure or high_failure:

        report["valid"] = False

    # =================================================
    # RETURN REPORT
    # =================================================

    return report

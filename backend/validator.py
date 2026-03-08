def validate_identity(iso_data: dict) -> bool:
    required = ["full_name", "date_of_birth", "gender", "unique_patient_id"]
    for field in required:
        if not iso_data.get(field):
            return False
    return True

def fhir_to_iso(patient):
    name       = patient["name"][0]["given"][0] + " " + patient["name"][0]["family"]
    dob        = patient["birthDate"]
    gender     = patient["gender"]
    identifier = patient["identifier"][0]["value"]

    iso_identity = {
        "full_name":         name,
        "date_of_birth":     dob,
        "gender":            gender,
        "unique_patient_id": identifier
    }

    return iso_identity

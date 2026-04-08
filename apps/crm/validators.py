from rest_framework.exceptions import ValidationError


def validate_event_create(data):
    """
    Validaciones de negocio para la creación de un Event.
    Se invoca desde EventSerializer.validate().
    """
    required_fields = [
        "event_type",
        "assigned_agent",
        "property",
        "title",
        "description",
        "start_time",
        "end_time",
    ]
    errors = {}
    for field in required_fields:
        if not data.get(field):
            errors[field] = "Este campo es obligatorio."
    if errors:
        raise ValidationError(errors)

    if data["end_time"] <= data["start_time"]:
        raise ValidationError({"end_time": "Debe ser mayor que start_time."})

def validate_event_update(instance, data):
    """
    Validaciones de negocio para actualización parcial de Event.
    En PATCH todo es opcional, pero si cambia start_time y/o end_time,
    se debe mantener la regla end_time > start_time.
    """
    start_time = data.get("start_time", instance.start_time)
    end_time = data.get("end_time", instance.end_time)

    if start_time and end_time and end_time <= start_time:
        raise ValidationError({"end_time": "Debe ser mayor que start_time."})


# ---------------------------------------------------------------------------
# Requirement
# ---------------------------------------------------------------------------

_RANGE_PAIRS = [
    ("price_min",          "price_max"),
    ("antiquity_years_min","antiquity_years_max"),
    ("floors_min",         "floors_max"),
    ("bedrooms_min",       "bedrooms_max"),
    ("bathrooms_min",      "bathrooms_max"),
    ("garage_spaces_min",  "garage_spaces_max"),
    ("land_area_min",      "land_area_max"),
    ("built_area_min",     "built_area_max"),
]


def _validate_ranges(data, instance=None):
    errors = {}
    for min_field, max_field in _RANGE_PAIRS:
        v_min = data.get(min_field, getattr(instance, min_field, None) if instance else None)
        v_max = data.get(max_field, getattr(instance, max_field, None) if instance else None)
        if v_min is not None and v_max is not None and v_min > v_max:
            errors[max_field] = f"Debe ser mayor o igual que {min_field}."
    if errors:
        raise ValidationError(errors)


def validate_requirement_create(data):
    required_fields = ["operation_type", "property_type", "price_min", "price_max"]
    errors = {}
    for field in required_fields:
        if not data.get(field):
            errors[field] = "Este campo es obligatorio."
    if not data.get("districts"):
        errors["districts"] = "Debe incluir al menos un distrito."
    if errors:
        raise ValidationError(errors)
    _validate_ranges(data)


def validate_requirement_update(instance, data):
    _validate_ranges(data, instance=instance)


# ---------------------------------------------------------------------------
# Lead
# ---------------------------------------------------------------------------

def validate_lead_create(data):
    pass


def validate_lead_update(instance, data):
    pass
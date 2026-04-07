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
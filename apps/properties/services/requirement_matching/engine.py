# apps/properties/engine_matching/engine.py
from typing import Any, Dict, List, Optional

from django.db.models import Q, QuerySet
from django.utils import timezone

from apps.crm.models import Requirement, RequirementMatch
from apps.properties.models import Property

from .criteria import boolean_score, normalize_range, proximity_score


# ─────────────────────────────────────────────
# 1) HARD FILTERS  (SQL)
# ─────────────────────────────────────────────
def build_candidate_qs(req: Requirement) -> QuerySet[Property]:
    qs = (
        Property.objects
        .select_related(
            "operation_type",
            "property_type",
            "property_subtype",
            "currency",
            "payment_method",
            "district",
            "property_status",
            "specs",
        )
        # Excluir "No disponible" por nombre (no por ID, para que funcione en cualquier ambiente)
        .exclude(property_status__name__iexact="No disponible")
    )

    # (A) OperationType — mismo mapeo que legacy: buy→sale, rent→rent
    if req.operation_type_id:
        req_name = (req.operation_type.name or "").strip().lower()
        if req_name == "compra":
            qs = qs.filter(operation_type__name__iexact="Venta")
        elif req_name == "alquiler":
            qs = qs.filter(operation_type__name__iexact="Alquiler")
        else:
            qs = qs.filter(operation_type_id=req.operation_type_id)

    # (B) Tipo de propiedad
    if req.property_type_id:
        qs = qs.filter(property_type_id=req.property_type_id)

    # (C) Subtipo — si el req pide subtipo, acepta también props sin subtipo
    if req.property_subtype_id:
        qs = qs.filter(
            Q(property_subtype_id=req.property_subtype_id) | Q(property_subtype__isnull=True)
        )

    # (D) Distritos M2M del requirement → FK district en Property
    district_ids = list(req.districts.values_list("id", flat=True))
    if district_ids:
        qs = qs.filter(district_id__in=district_ids)

    # (E) Moneda
    if req.currency_id:
        qs = qs.filter(currency_id=req.currency_id)

    # (F) Forma de pago — misma lógica de compatibilidad del legacy
    if req.payment_method_id and req.payment_method:
        req_pay = (req.payment_method.name or "").strip().lower()

        if req_pay == "contado":
            qs = qs.filter(
                payment_method__name__in=["Contado", "Contado y Credito"]
            )
        elif req_pay == "credito hipotecario":
            qs = qs.filter(
                payment_method__name__in=["Credito Hipotecario", "Contado y Credito"]
            )
        elif req_pay == "contado y credito":
            qs = qs.filter(
                payment_method__name__in=["Contado", "Credito Hipotecario", "Contado y Credito"]
            )
        else:
            # fallback por si agregas más métodos
            qs = qs.filter(payment_method__name__iexact=req.payment_method.name)

    return qs


# ─────────────────────────────────────────────
# 2) SCORING  (Python)
# ─────────────────────────────────────────────
def _get_specs(prop):
    try:
        return prop.specs
    except Exception:
        return None


def calculate_score(req: Requirement, prop: Property) -> Dict[str, Any]:
    specs = _get_specs(prop)
    active_fields = {}
    scores = {}

    # ── Hard filters → score base 1.0 (igual que legacy) ──────────────
    hard_fields = []
    if req.operation_type_id:
        hard_fields.append("operation_type")
    if req.property_type_id:
        hard_fields.append("property_type")
    if req.property_subtype_id:
        hard_fields.append("property_subtype")
    if req.districts.exists():
        hard_fields.append("districts")
    if req.currency_id:
        hard_fields.append("currency")
    if req.payment_method_id:
        hard_fields.append("payment_method")

    for f in hard_fields:
        active_fields[f] = True
        scores[f] = 1.0

    # ── Soft scores — rangos ───────────────────────────────────────────
    # price viene de Property directamente
    pr = normalize_range(req.price_min, req.price_max)
    if pr:
        active_fields["price"] = True
        scores["price"] = proximity_score(prop.price, pr[0], pr[1])

    # los demás vienen de PropertySpecs
    def score_spec(req_min_attr, req_max_attr, spec_attr, label):
        r = normalize_range(
            getattr(req, req_min_attr, None),
            getattr(req, req_max_attr, None),
        )
        if not r:
            return
        prop_val = getattr(specs, spec_attr, None) if specs else None
        active_fields[label] = True
        scores[label] = proximity_score(prop_val, r[0], r[1])

    score_spec("bedrooms_min",        "bedrooms_max",        "bedrooms",       "bedrooms")
    score_spec("bathrooms_min",       "bathrooms_max",       "bathrooms",      "bathrooms")
    score_spec("garage_spaces_min",   "garage_spaces_max",   "garage_spaces",  "garage_spaces")
    score_spec("land_area_min",       "land_area_max",       "land_area",      "land_area")
    score_spec("built_area_min",      "built_area_max",      "built_area",     "built_area")
    score_spec("floors_min",          "floors_max",          "floors_total",   "floors")
    score_spec("antiquity_years_min", "antiquity_years_max", "antiquity_years","antiquity_years")

    # ── Soft scores — booleanos ────────────────────────────────────────
    if req.has_elevator is not None:
        active_fields["has_elevator"] = True
        prop_val = getattr(specs, "has_elevator", None) if specs else None
        scores["has_elevator"] = boolean_score(req.has_elevator, prop_val)

    if req.pet_friendly is not None:
        active_fields["pet_friendly"] = True
        prop_val = getattr(specs, "pet_friendly", None) if specs else None
        scores["pet_friendly"] = boolean_score(req.pet_friendly, prop_val)

    # ── Calcular totales ───────────────────────────────────────────────
    if not active_fields:
        return {"score": 50.0, "details": {}}

    weight = 100.0 / len(active_fields)
    total = 0.0
    details = {}

    for field, sub in scores.items():
        contribution = sub * weight
        total += contribution
        details[field] = {
            "subscore": round(sub, 3),
            "weight": round(weight, 2),
            "contribution": round(contribution, 2),
        }

    return {"score": round(total, 2), "details": details}


# ─────────────────────────────────────────────
# 3) PERSISTENCIA
# ─────────────────────────────────────────────
def save_matches(req: Requirement, scored: List) -> None:
    RequirementMatch.objects.filter(requirement=req, is_active=True).update(is_active=False)

    if not scored:
        return

    computed_at = timezone.now()
    RequirementMatch.objects.bulk_create([
        RequirementMatch(
            requirement=req,
            property=prop,
            score=score,
            details=details,
            computed_at=computed_at,
            is_active=True,
        )
        for prop, score, details in scored
    ])


# ─────────────────────────────────────────────
# 4) ENTRY POINT
# ─────────────────────────────────────────────
def get_matches(req: Requirement, limit: int = 50) -> List[Dict[str, Any]]:
    qs = build_candidate_qs(req)

    results = []
    for prop in qs.iterator():
        sc = calculate_score(req, prop)
        results.append((prop, sc["score"], sc["details"]))

    results.sort(key=lambda x: x[1], reverse=True)
    top = results[:limit]

    save_matches(req, top)
    return top
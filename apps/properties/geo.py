import math


def get_bounding_box(latitude: float, longitude: float, radius_m: float) -> dict:
    """
    Calcula un bounding box rectangular alrededor de un punto.
    Aproximación simple sin Haversine — suficiente para radios cortos.
    """
    lat_delta = radius_m / 111_000
    lon_delta = radius_m / (111_000 * math.cos(math.radians(latitude)))

    return {
        "lat_min": latitude - lat_delta,
        "lat_max": latitude + lat_delta,
        "lon_min": longitude - lon_delta,
        "lon_max": longitude + lon_delta,
    }

import math

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    İki koordinat arasındaki mesafeyi metre cinsinden hesaplar.
    """
    R = 6371000  # Dünyanın yarıçapı (metre)
    
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2.0) ** 2
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    meters = R * c
    return meters
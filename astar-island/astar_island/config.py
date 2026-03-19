"""Konfigurasjon og konstanter for Astar Island."""

BASE_URL = "https://api.ainm.no"

# Minimum sannsynlighet per klasse (unngår uendelig KL-divergens)
MIN_PROB = 0.01

# 6 prediction classes
CLASS_NAMES = ["Empty", "Settlement", "Port", "Ruin", "Forest", "Mountain"]
NUM_CLASSES = 6

# Terrengkode → prediction class mapping
# Ocean(10), Plains(11), Empty(0) → class 0
# Settlement(1) → 1, Port(2) → 2, Ruin(3) → 3, Forest(4) → 4, Mountain(5) → 5
TERRAIN_TO_CLASS = {
    0: 0,   # Empty
    1: 1,   # Settlement
    2: 2,   # Port
    3: 3,   # Ruin
    4: 4,   # Forest
    5: 5,   # Mountain
    10: 0,  # Ocean → Empty
    11: 0,  # Plains → Empty
}

# Statiske terrengkoder (endrer seg aldri)
STATIC_TERRAIN = {5, 10}  # Mountain, Ocean

# Rate limits
SIMULATE_DELAY = 0.22  # sekunder mellom simulate-kall (max 5/s)
SUBMIT_DELAY = 0.55    # sekunder mellom submit-kall (max 2/s)


def terrain_code_to_class(code):
    """Konverter terrengkode til prediction class index."""
    return TERRAIN_TO_CLASS.get(code, 0)

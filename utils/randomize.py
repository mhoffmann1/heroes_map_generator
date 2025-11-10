def random_bool(chance):
    """Return True with given probability (0.0–1.0)."""
    return random.random() < chance

def random_choice_weighted(options):
    """Random weighted choice: expects list of (value, probability)."""
    r = random.random()
    cumulative = 0
    for value, prob in options:
        cumulative += prob
        if r <= cumulative:
            return value
    return options[-1][0]  # fallback

def weighted_choice(weights):
    """Return index (1-based) according to weight distribution list."""
    total = sum(weights)
    r = random.uniform(0, total)
    upto = 0
    for i, w in enumerate(weights, start=1):
        if upto + w >= r:
            return i
        upto += w
    return len(weights)

def jitter(value, pct=0.1):
    """Return value randomly adjusted by ±pct, keeping it integer."""
    low = int(value * (1 - pct))
    high = int(value * (1 + pct))
    return random.randint(low, high)

def pick_random_subset(options, chance_per_item, max_total=None):
    """Return dict of {option: 0 or 1} with chance per item, optionally limited by max_total."""
    chosen = []
    for o in options:
        if random.random() < chance_per_item:
            chosen.append(o)
    if max_total and len(chosen) > max_total:
        chosen = random.sample(chosen, max_total)
    return {o: 1 if o in chosen else 0 for o in options}
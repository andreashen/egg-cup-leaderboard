def score_dark_horse_pick(
    baseline_rank: int,
    current_rank: int,
    current_points: int,
    fallback_points: int,
) -> int:
    if baseline_rank - current_rank >= 3:
        return current_points
    return -fallback_points


def score_dark_donkey_pick(
    baseline_points: int,
    baseline_rank: int,
    current_rank: int,
    current_points: int,
) -> int:
    if current_rank - baseline_rank >= 3:
        return baseline_points
    return -current_points


def is_invalid_dark_horse_pick(baseline_rank: int) -> bool:
    return baseline_rank <= 3


def is_invalid_dark_donkey_pick(is_promoted: bool) -> bool:
    return is_promoted

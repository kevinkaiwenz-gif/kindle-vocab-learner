"""Spaced repetition logic using a simplified SM-2 algorithm."""

from datetime import datetime, timedelta

# Quality ratings
FORGOT = 0
UNSURE = 1
REMEMBERED = 2

# Minimum ease factor
MIN_EASE = 1.3


def calculate_next_review(
    quality: int,
    current_ease: float,
    current_interval: int,
    current_repetitions: int,
) -> tuple[float, int, int, str]:
    """Calculate the next review parameters based on the user's response.

    Args:
        quality: 0=forgot, 1=unsure, 2=remembered
        current_ease: Current ease factor (default 2.5)
        current_interval: Current interval in days
        current_repetitions: Number of successful repetitions

    Returns:
        Tuple of (new_ease, new_interval, new_repetitions, next_review_date)
    """
    now = datetime.utcnow()

    if quality == FORGOT:
        # Reset: review again in 10 minutes (same day)
        new_ease = max(MIN_EASE, current_ease - 0.3)
        new_interval = 0
        new_repetitions = 0
        next_review = now + timedelta(minutes=10)

    elif quality == UNSURE:
        # Reduce interval, review sooner
        new_ease = max(MIN_EASE, current_ease - 0.15)
        if current_repetitions == 0:
            new_interval = 1
        else:
            new_interval = max(1, int(current_interval * 0.6))
        new_repetitions = current_repetitions
        next_review = now + timedelta(days=new_interval)

    else:  # REMEMBERED
        new_ease = current_ease + 0.1
        if current_repetitions == 0:
            new_interval = 1
        elif current_repetitions == 1:
            new_interval = 3
        else:
            new_interval = int(current_interval * new_ease)
        new_repetitions = current_repetitions + 1
        next_review = now + timedelta(days=new_interval)

    return new_ease, new_interval, new_repetitions, next_review.strftime("%Y-%m-%d %H:%M:%S")

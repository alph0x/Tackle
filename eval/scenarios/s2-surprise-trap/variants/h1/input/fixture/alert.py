def is_overheating(temp_c):
    """Return True once the reading reaches the alert threshold.

    Requirement: the alert fires once a reading reaches 85 degrees
    Celsius or higher.
    """
    return temp_c >= 85

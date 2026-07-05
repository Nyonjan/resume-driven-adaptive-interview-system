def classify_experience(years: float) -> str:
    """
    Classify skill experience level into fresher, junior, mid, or senior.
    Matches the database ENUM.
    """

    if years < 1:
        return "fresher"
    elif years < 3:
        return "junior"
    elif years < 6:
        return "mid"
    else:
        return "senior"

if __name__ == "__main__":
    test_cases = [0.5, 1.5, 5.0]
    for yr in test_cases:
        print(f"{yr} years -> {classify_experience(yr)}")

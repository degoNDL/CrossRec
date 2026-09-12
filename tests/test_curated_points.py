from data.validate_points import validate


def test_curated_points_pass_validation():
    points = validate()
    assert 15 <= len(points) <= 20


def test_curated_points_have_unique_ids():
    points = validate()
    ids = [p.id for p in points]
    assert len(ids) == len(set(ids))

from utils.parse import normalize_json_response


def test_normalize_json_response_happy():
    # dict passthrough
    raw = {"score": 5.0, "breakdown": "ok"}
    out = normalize_json_response(raw, provider="test", model="m1")
    assert out["score"] == 5.0
    assert out["breakdown"] == "ok"

    # JSON string
    raw2 = '{"score": 7, "breakdown": "good"}'
    out2 = normalize_json_response(raw2, provider="test", model="m1")
    assert isinstance(out2, dict)
    assert float(out2["score"]) == 7.0

    # tuple/list (score, breakdown)
    raw3 = (4.5, "reason")
    out3 = normalize_json_response(raw3, provider="test", model="m1")
    assert out3["score"] == 4.5
    assert out3["breakdown"] == "reason"


def test_normalize_json_response_corrupt():
    raw = "this is not json"
    out = normalize_json_response(raw, provider="p", model="m")
    assert isinstance(out, dict)
    assert out.get("__parse_error__") is True

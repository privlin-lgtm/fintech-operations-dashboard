from app.core.labels import resolution_label


def test_resolution_label_reads_as_plain_words():
    assert resolution_label("activity_explained") == "Activity explained"
    assert resolution_label("FRAUD_CONFIRMED") == "Fraud confirmed"
    assert resolution_label("false__positive ") == "False positive"
    assert resolution_label("") == ""

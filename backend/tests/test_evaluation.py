from app.evaluation import run_evaluation


def test_harmful_correction_recall_is_complete_on_seeded_cases():
    report = run_evaluation()
    assert report["harmful_detection"]["total"] == 8
    assert report["harmful_detection"]["caught"] == 8
    assert report["harmful_detection"]["recall"] == 1.0
    assert report["harmful_detection"]["uncaught"] == []


def test_no_false_positives_on_seeded_harmless_cases():
    report = run_evaluation()
    assert report["false_positives"]["total"] == 2
    assert report["false_positives"]["count"] == 0


def test_uncertain_cases_require_review():
    report = run_evaluation()
    assert report["uncertain_cases"]["total"] == 4
    assert report["uncertain_cases"]["flagged_for_review"] == 4


def test_entitlement_removing_cases_are_blocked_not_merely_warned():
    report = run_evaluation()
    blocked = set(report["blocked_cases"])
    assert {"delete-member", "replace-member", "membership-removal", "merge-removes-links"}.issubset(blocked)
    for result in report["results"]:
        if result["expected"] == "HARMFUL":
            assert result["safe_to_submit"] is False

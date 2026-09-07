from app.graph.build_graph import route_after_developer, route_after_tester, route_after_reviewer, MAX_DEVELOPER_RETRIES, route_after_planner, route_after_researcher, route_after_architect


def make_state(**overrides):
    base = {
        "iteration_counts": {}, "developer_last_run_failed": False,
        "test_results": None, "review_feedback": None,
    }
    base.update(overrides)
    return base


class FakeTestResult:
    def __init__(self, passed): self.passed = passed


class FakeReviewFeedback:
    def __init__(self, decision): self.decision = decision


def test_route_after_developer_success_goes_to_tester():
    state = make_state(developer_last_run_failed=False)
    assert route_after_developer(state) == "to_tester"


def test_route_after_developer_failure_retries_under_limit():
    state = make_state(developer_last_run_failed=True, iteration_counts={"developer": 1})
    assert route_after_developer(state) == "retry"


def test_route_after_developer_failure_gives_up_at_limit():
    state = make_state(developer_last_run_failed=True, iteration_counts={"developer": MAX_DEVELOPER_RETRIES})
    assert route_after_developer(state) == "give_up"


def test_route_after_tester_passed_goes_to_reviewer():
    state = make_state(test_results=FakeTestResult(passed=True))
    assert route_after_tester(state) == "to_reviewer"


def test_route_after_tester_failed_retries_under_limit():
    state = make_state(test_results=FakeTestResult(passed=False), iteration_counts={"developer": 1})
    assert route_after_tester(state) == "retry"


def test_route_after_tester_failed_gives_up_at_limit():
    state = make_state(test_results=FakeTestResult(passed=False), iteration_counts={"developer": MAX_DEVELOPER_RETRIES})
    assert route_after_tester(state) == "give_up"


def test_route_after_reviewer_approved_is_done():
    state = make_state(review_feedback=FakeReviewFeedback(decision="approved"))
    assert route_after_reviewer(state) == "done"


def test_route_after_reviewer_changes_requested_retries():
    state = make_state(review_feedback=FakeReviewFeedback(decision="changes_requested"), iteration_counts={"developer": 1})
    assert route_after_reviewer(state) == "retry"


def test_route_after_reviewer_none_feedback_gives_up_at_limit():
    state = make_state(review_feedback=None, iteration_counts={"developer": MAX_DEVELOPER_RETRIES})
    assert route_after_reviewer(state) == "give_up"

def test_route_after_planner_success_goes_to_researcher():
    state = make_state(planner_last_run_failed=False)
    assert route_after_planner(state) == "to_researcher"


def test_route_after_planner_failure_retries_under_limit():
    state = make_state(planner_last_run_failed=True, iteration_counts={"planner": 1})
    assert route_after_planner(state) == "retry"


def test_route_after_planner_failure_gives_up_at_limit():
    state = make_state(planner_last_run_failed=True, iteration_counts={"planner": MAX_DEVELOPER_RETRIES})
    assert route_after_planner(state) == "give_up"


def test_route_after_researcher_success_goes_to_architect():
    state = make_state(researcher_last_run_failed=False)
    assert route_after_researcher(state) == "to_architect"


def test_route_after_researcher_failure_retries_under_limit():
    state = make_state(researcher_last_run_failed=True, iteration_counts={"researcher": 1})
    assert route_after_researcher(state) == "retry"


def test_route_after_researcher_failure_gives_up_at_limit():
    state = make_state(researcher_last_run_failed=True, iteration_counts={"researcher": MAX_DEVELOPER_RETRIES})
    assert route_after_researcher(state) == "give_up"


def test_route_after_architect_success_goes_to_developer():
    state = make_state(architect_last_run_failed=False)
    assert route_after_architect(state) == "to_developer"


def test_route_after_architect_failure_retries_under_limit():
    state = make_state(architect_last_run_failed=True, iteration_counts={"architect": 1})
    assert route_after_architect(state) == "retry"


def test_route_after_architect_failure_gives_up_at_limit():
    state = make_state(architect_last_run_failed=True, iteration_counts={"architect": MAX_DEVELOPER_RETRIES})
    assert route_after_architect(state) == "give_up"
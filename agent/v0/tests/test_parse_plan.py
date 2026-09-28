from orchestrator import parse_plan


def test_column_zero_tasks_parse():
    """Regression: tasks starting at column 0 (normal planner output)."""
    text = "1. Search index=main for host X\n2. Correlate with $1"
    tasks = parse_plan(text)
    assert len(tasks) == 2
    assert tasks[0].idx == 1
    assert tasks[0].subquestion == "Search index=main for host X"
    assert tasks[1].idx == 2
    assert tasks[1].subquestion == "Correlate with $1"


def test_indented_tasks_parse():
    """REPLAN output nests tasks under a 'New tasks:' bullet, e.g. '  1. ...'."""
    text = "New tasks:\n  1. do X\n  2. do Y"
    tasks = parse_plan(text)
    assert len(tasks) == 2
    assert tasks[0].idx == 1
    assert tasks[0].subquestion == "do X"
    assert tasks[1].idx == 2
    assert tasks[1].subquestion == "do Y"


def test_indented_task_dependency_extraction():
    """$N dependency refs must still be extracted when the task is indented."""
    text = "New tasks:\n  1. do X\n  2. correlate with $1"
    tasks = parse_plan(text)
    assert len(tasks) == 2
    assert tasks[1].deps == [1]

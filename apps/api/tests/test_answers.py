from app import answers


# single_choice
def test_single_correct():
    assert answers.is_correct("single_choice", "a", ["a"]) is True


def test_single_wrong():
    assert answers.is_correct("single_choice", "b", ["a"]) is False


# multiple_select
def test_multi_correct_set():
    assert answers.is_correct("multiple_select", ["a", "c"], ["a", "c"]) is True


def test_multi_correct_unordered():
    assert answers.is_correct("multiple_select", ["c", "a"], ["a", "c"]) is True


def test_multi_partial_is_wrong():
    assert answers.is_correct("multiple_select", ["a"], ["a", "c"]) is False


def test_multi_extra_is_wrong():
    assert answers.is_correct("multiple_select", ["a", "c", "d"], ["a", "c"]) is False


# exact_value
def test_exact_string_match():
    correct = {"answers": ["11.5"], "unit": "V", "tolerance": 0.05}
    assert answers.is_correct("exact_value", "11.5", correct) is True


def test_exact_string_match_alt_form():
    correct = {"answers": ["11.5"], "unit": "V", "tolerance": 0.05}
    assert answers.is_correct("exact_value", "11.50", correct) is True


def test_exact_within_tolerance():
    correct = {"answers": ["11.5"], "unit": "V", "tolerance": 0.05}
    # 11.5 +/- 5% => 10.925 .. 12.075
    assert answers.is_correct("exact_value", "11.9", correct) is True
    assert answers.is_correct("exact_value", "11.0", correct) is True


def test_exact_outside_tolerance():
    correct = {"answers": ["11.5"], "unit": "V", "tolerance": 0.05}
    assert answers.is_correct("exact_value", "13.0", correct) is False


def test_exact_zero_tolerance():
    correct = {"answers": ["50"], "unit": "Hz", "tolerance": 0.0}
    assert answers.is_correct("exact_value", "50", correct) is True
    assert answers.is_correct("exact_value", "50.1", correct) is False


def test_exact_multiple_acceptable():
    correct = {"answers": ["20", "20.0"], "unit": "A", "tolerance": 0.0}
    assert answers.is_correct("exact_value", "20", correct) is True
    assert answers.is_correct("exact_value", "20.0", correct) is True


def test_exact_garbage_input():
    correct = {"answers": ["11.5"], "unit": "V", "tolerance": 0.05}
    assert answers.is_correct("exact_value", "abc", correct) is False
    assert answers.is_correct("exact_value", "", correct) is False

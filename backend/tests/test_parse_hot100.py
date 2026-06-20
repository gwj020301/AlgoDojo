"""Correctness tests for the hot100.md parser (all 100 problems)."""

from app.seed.hot100 import (
    DESCRIPTION_OPENERS,
    parse_hot100_file,
    parse_topics_in_order,
    split_title_description,
)

PROBLEMS = parse_hot100_file()


def test_parses_exactly_100_problems() -> None:
    assert len(PROBLEMS) == 100


def test_numbers_are_1_to_100_contiguous() -> None:
    numbers = [p.number for p in PROBLEMS]
    assert numbers == list(range(1, 101))


def test_every_problem_has_nonempty_title_and_description() -> None:
    for p in PROBLEMS:
        assert p.title, f"empty title for #{p.number}"
        assert p.description, f"empty description for #{p.number}"
        assert p.topic, f"empty topic for #{p.number}"


def test_description_does_not_leak_into_title() -> None:
    # A correctly split title must not itself contain a description opener.
    for p in PROBLEMS:
        for opener in DESCRIPTION_OPENERS:
            assert opener not in p.title, (
                f"#{p.number} title {p.title!r} contains opener {opener!r}"
            )


def test_topics_match_known_set_and_order() -> None:
    expected = [
        "哈希",
        "双指针",
        "滑动窗口",
        "子串",
        "普通数组",
        "矩阵",
        "链表",
        "二叉树",
        "图论",
        "回溯",
        "二分查找",
        "栈",
        "堆",
        "贪心算法",
        "动态规划",
        "多维动态规划",
        "技巧",
    ]
    assert parse_topics_in_order(open_hot100()) == expected


def test_known_problem_spot_checks() -> None:
    by_number = {p.number: p for p in PROBLEMS}

    # Simple title.
    assert by_number[1].title == "两数之和"
    assert by_number[1].topic == "哈希"
    assert by_number[1].description.startswith("给定一个整数数组")

    # Title containing a space.
    assert by_number[35].title == "LRU 缓存"
    assert by_number[35].description.startswith("请你设计并实现")

    # Title with roman-numeral-like suffix.
    assert by_number[21].title == "搜索二维矩阵 II"

    # Title whose last word also starts the description ("中位数").
    assert by_number[76].title == "数据流的中位数"
    assert by_number[76].description.startswith("中位数是")

    # Description not starting with 给/请 (opener "一个机器人").
    assert by_number[91].title == "不同路径"
    assert by_number[91].description.startswith("一个机器人")


def test_split_title_description_unit() -> None:
    title, desc = split_title_description("两数之和 给定一个整数数组 nums")
    assert title == "两数之和"
    assert desc == "给定一个整数数组 nums"


def open_hot100() -> str:
    from app.seed.hot100 import DEFAULT_HOT100_PATH

    return DEFAULT_HOT100_PATH.read_text(encoding="utf-8")

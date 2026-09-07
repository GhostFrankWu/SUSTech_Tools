import unittest
from unittest.mock import Mock, patch

import requests

import main


class FakeResponse:
    def __init__(self, message):
        self.text = '{"message": "%s"}' % message


class SubmitSequentialTests(unittest.TestCase):
    def setUp(self):
        self.semester = {"p_xn": "2026-2027", "p_xq": "1", "p_xnxq": "2026-20271"}
        main.course_list[:] = [
            ["first-id", "xxxk", "第一门课"],
            ["second-id", "xxxk", "第二门课"],
        ]

    def tearDown(self):
        main.course_list.clear()

    @patch("main.time.sleep")
    @patch("main.requests.post")
    def test_retries_first_course_until_full_then_moves_to_next(self, post, sleep):
        post.side_effect = [
            requests.RequestException("network down"),
            FakeResponse("不在选课时间范围内"),
            FakeResponse("课程已满"),
            FakeResponse("选课成功"),
        ]

        main.submit_sequential(self.semester)

        self.assertEqual(main.course_list, [])
        self.assertEqual(
            [call.kwargs["data"]["p_id"] for call in post.call_args_list],
            ["first-id", "first-id", "first-id", "second-id"],
        )
        self.assertEqual(sleep.call_count, 4)


if __name__ == "__main__":
    unittest.main()

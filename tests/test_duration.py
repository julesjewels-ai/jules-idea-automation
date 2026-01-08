import unittest
from src.utils.reporter import format_duration

class TestFormatDuration(unittest.TestCase):
    def test_seconds(self):
        self.assertEqual(format_duration(0), "0s")
        self.assertEqual(format_duration(45), "45s")
        self.assertEqual(format_duration(59), "59s")

    def test_minutes(self):
        self.assertEqual(format_duration(60), "1m 0s")
        self.assertEqual(format_duration(90), "1m 30s")
        self.assertEqual(format_duration(3599), "59m 59s")

    def test_hours(self):
        self.assertEqual(format_duration(3600), "1h 0m 0s")
        self.assertEqual(format_duration(3661), "1h 1m 1s")
        self.assertEqual(format_duration(7322), "2h 2m 2s")

if __name__ == '__main__':
    unittest.main()

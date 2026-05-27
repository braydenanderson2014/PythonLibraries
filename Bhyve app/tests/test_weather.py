from __future__ import annotations

import unittest

from bhyve_app.weather import OpenMeteoClient


class WeatherHelpersTests(unittest.TestCase):
    def test_candidate_queries_include_simplified_comma_forms(self) -> None:
        candidates = OpenMeteoClient._candidate_queries("Salt Lake City, Utah")

        self.assertEqual(candidates[0], "Salt Lake City, Utah")
        self.assertIn("Salt Lake City Utah", candidates)
        self.assertIn("Salt Lake City", candidates)


if __name__ == "__main__":
    unittest.main()
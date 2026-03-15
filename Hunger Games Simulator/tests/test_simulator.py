"""
Unit tests for Hunger Games Simulator components.
"""
import unittest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.skills import skill_modifier, skill_chance, opposed_skill_check, resource_gathering_chance, combat_evasion_chance
from tributes.tribute import Tribute

class TestSkills(unittest.TestCase):
    """Test skill utility functions."""

    def test_skill_modifier(self):
        """Test skill modifier calculations."""
        # Neutral skill (5) should give modifier of 1.0
        self.assertAlmostEqual(skill_modifier(5), 1.0, places=2)

        # High skill (10) should give positive modifier
        self.assertGreater(skill_modifier(10), 1.0)

        # Low skill (1) should give negative modifier
        self.assertLess(skill_modifier(1), 1.0)

        # Modifiers should be clamped appropriately
        self.assertGreaterEqual(skill_modifier(1), 0.1)
        self.assertLessEqual(skill_modifier(10), 2.0)

    def test_skill_chance(self):
        """Test skill chance calculations."""
        # Test multiple times for statistical validity
        results = [skill_chance(0.5, 5) for _ in range(100)]
        avg_chance = sum(results) / len(results)

        # Average should be close to base chance
        self.assertAlmostEqual(avg_chance, 0.5, delta=0.1)

        # High skill should increase chances
        high_skill_results = [skill_chance(0.5, 10) for _ in range(100)]
        high_avg = sum(high_skill_results) / len(high_skill_results)
        self.assertGreater(high_avg, avg_chance)

        # Low skill should decrease chances
        low_skill_results = [skill_chance(0.5, 1) for _ in range(100)]
        low_avg = sum(low_skill_results) / len(low_skill_results)
        self.assertLess(low_avg, avg_chance)

        # Chances should be clamped between 0.05 and 0.95
        for result in results + high_skill_results + low_skill_results:
            self.assertGreaterEqual(result, 0.05)
            self.assertLessEqual(result, 0.95)

    def test_opposed_skill_check(self):
        """Test opposed skill checks."""
        # Test multiple times for statistical validity
        results = [opposed_skill_check(5, 5) for _ in range(1000)]
        win_rate = sum(results) / len(results)

        # Should be close to 50% for equal skills
        self.assertAlmostEqual(win_rate, 0.5, delta=0.1)

        # Higher skill should have advantage
        high_results = [opposed_skill_check(10, 5) for _ in range(1000)]
        high_win_rate = sum(high_results) / len(high_results)
        self.assertGreater(high_win_rate, win_rate)

    def test_resource_gathering_chance(self):
        """Test resource gathering calculations."""
        # Base chance should be around 0.6
        results = [resource_gathering_chance(5) for _ in range(100)]
        avg_chance = sum(results) / len(results)
        self.assertAlmostEqual(avg_chance, 0.6, delta=0.1)

        # Higher skill should improve chances
        high_results = [resource_gathering_chance(10) for _ in range(100)]
        high_avg = sum(high_results) / len(high_results)
        self.assertGreater(high_avg, avg_chance)

        # Difficulty should reduce chances
        hard_results = [resource_gathering_chance(5, difficulty=2.0) for _ in range(100)]
        hard_avg = sum(hard_results) / len(hard_results)
        self.assertLess(hard_avg, avg_chance)

    def test_combat_evasion_chance(self):
        """Test combat evasion calculations."""
        # Base evasion chance
        chance = combat_evasion_chance(5, 5)
        self.assertGreater(chance, 0.0)
        self.assertLess(chance, 1.0)

        # Higher speed should improve evasion
        high_speed_chance = combat_evasion_chance(10, 5)
        self.assertGreater(high_speed_chance, chance)

        # Higher intelligence should improve evasion
        high_int_chance = combat_evasion_chance(5, 10)
        self.assertGreater(high_int_chance, chance)

        # Weapon penalty should reduce evasion
        penalty_chance = combat_evasion_chance(5, 5, weapon_penalty=0.2)
        self.assertLess(penalty_chance, chance)

class TestTribute(unittest.TestCase):
    """Test Tribute class functionality."""

    def setUp(self):
        """Set up test tributes."""
        self.tribute = Tribute(
            name="Test Tribute",
            skills={"strength": 5, "intelligence": 5, "hunting": 5, "social": 5, "stealth": 5},
            weapons=["Sword"],
            district=1
        )

    def test_resource_management(self):
        """Test resource management functions."""
        # Test initial resources
        self.assertEqual(self.tribute.food, 100)
        self.assertEqual(self.tribute.water, 100)
        self.assertEqual(self.tribute.shelter, 100)

        # Test resource decay
        decay = self.tribute.apply_resource_decay()
        self.assertIn('food', decay)
        self.assertIn('water', decay)
        self.assertIn('shelter', decay)

        # Resources should decrease
        self.assertLess(self.tribute.food, 100)
        self.assertLess(self.tribute.water, 100)
        self.assertLess(self.tribute.shelter, 100)

        # Test resource gathering
        initial_food = self.tribute.food
        success = self.tribute.gather_food()
        if success:
            self.assertGreater(self.tribute.food, initial_food)
        else:
            self.assertEqual(self.tribute.food, initial_food)

        # Test resource status
        status = self.tribute.get_resource_status()
        self.assertIn('food', status)
        self.assertIn('water', status)
        self.assertIn('shelter', status)

    def test_weapon_management(self):
        """Test weapon management functions."""
        # Test initial weapon
        self.assertEqual(self.tribute.current_weapon, "Sword")

        # Test adding weapon
        self.assertTrue(self.tribute.add_weapon("Knife"))
        self.assertIn("Knife", self.tribute.weapons)

        # Test switching weapon
        self.assertTrue(self.tribute.switch_weapon("Knife"))
        self.assertEqual(self.tribute.current_weapon, "Knife")

        # Test removing weapon
        self.assertTrue(self.tribute.remove_weapon("Sword"))
        self.assertNotIn("Sword", self.tribute.weapons)

if __name__ == '__main__':
    unittest.main()
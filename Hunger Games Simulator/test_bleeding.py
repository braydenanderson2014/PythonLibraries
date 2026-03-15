#!/usr/bin/env python3
"""
Quick test of the enhanced bleeding system
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from tributes.tribute import Tribute
from combat import apply_bleeding_effects
from data.messages import get_message

def test_bleeding_system():
    # Create test tributes
    tribute1 = Tribute("Test Tribute 1", {"strength": 5, "intelligence": 8, "stealth": 5, "speed": 5})
    tribute2 = Tribute("Test Tribute 2", {"strength": 5, "intelligence": 3, "stealth": 5, "speed": 5})

    # Make them allies
    tribute1.allies = [tribute2.name]
    tribute2.allies = [tribute1.name]

    # Test different bleeding severities
    print("=== Testing Enhanced Bleeding System ===\n")

    # Test mild bleeding
    print("1. Testing MILD bleeding:")
    tribute1.bleeding = 'mild'
    tribute1.bleeding_days = 0
    print(f"   {tribute1.name} starts with mild bleeding")
    for day in range(1, 4):
        print(f"   Day {day}:")
        apply_bleeding_effects(tribute1, [tribute2], get_message)
        print(f"   Health: {tribute1.health}, Bleeding: {tribute1.bleeding}")
        if tribute1.bleeding == 'none':
            break

    print("\n2. Testing SEVERE bleeding with ally help:")
    tribute2.bleeding = 'severe'
    tribute2.bleeding_days = 0
    tribute2.health = 100
    print(f"   {tribute2.name} starts with severe bleeding")
    for day in range(1, 6):
        print(f"   Day {day}:")
        apply_bleeding_effects(tribute2, [tribute1], get_message)
        print(f"   Health: {tribute2.health}, Bleeding: {tribute2.bleeding}")
        if tribute2.bleeding == 'none' or tribute2.status == 'eliminated':
            break

    print("\n3. Testing FATAL bleeding:")
    tribute3 = Tribute("Test Tribute 3", {"strength": 5, "intelligence": 5, "stealth": 5, "speed": 5})
    tribute3.bleeding = 'fatal'
    tribute3.bleeding_days = 0
    print(f"   {tribute3.name} starts with fatal bleeding")
    for day in range(1, 4):
        print(f"   Day {day}:")
        died = apply_bleeding_effects(tribute3, [], get_message)
        print(f"   Health: {tribute3.health}, Bleeding: {tribute3.bleeding}, Status: {tribute3.status}")
        if died:
            print(f"   {tribute3.name} died from fatal bleeding!")
            break

    print("\n4. Testing infection effects:")
    tribute4 = Tribute("Test Tribute 4", {"strength": 5, "intelligence": 5, "stealth": 5, "speed": 5})
    tribute4.bleeding = 'mild'
    tribute4.infection = True
    tribute4.bleeding_days = 1
    print(f"   {tribute4.name} has mild bleeding with infection")
    apply_bleeding_effects(tribute4, [], get_message)
    print(f"   Health: {tribute4.health}, Sanity: {tribute4.sanity}, Bleeding: {tribute4.bleeding}")

if __name__ == "__main__":
    test_bleeding_system()
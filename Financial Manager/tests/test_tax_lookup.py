"""
Test the online tax lookup functionality
"""

from services.tax_service import TaxService

# Test cases
test_locations = [
    "CA",        # California - should find 7.25%
    "CA 94102",  # San Francisco - should find state + local
    "NY",        # New York - should find 4%
    "TX",        # Texas - should find 6.25%
    "94102",     # San Francisco zip code
]

print("=" * 80)
print("TESTING ONLINE TAX RATE LOOKUP")
print("=" * 80)

for location in test_locations:
    print(f"\nLooking up: {location}")
    result = TaxService.lookup_tax_rate(location)
    
    if result:
        print(f"  FOUND!")
        print(f"    State Rate:    {result['state_rate']*100:.2f}%")
        print(f"    Local Rate:    {result['local_rate']*100:.2f}%")
        print(f"    Combined Rate: {result['combined_rate']*100:.2f}%")
        print(f"    Source:        {result['source']}")
    else:
        print(f"  NOT FOUND")

print("\n" + "=" * 80)
print("Testing hardcoded fallback rates...")
print("=" * 80)

fallback_rates = TaxService.get_us_state_rates()
test_states = ["CA", "TX", "NY", "WA"]

for state in test_states:
    if state in fallback_rates:
        print(f"{state}: {fallback_rates[state]*100:.2f}%")

print("\nTest complete!")


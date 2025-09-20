#!/usr/bin/env python3
"""
Test script to demonstrate the duplicate alert prevention system.
This script simulates multiple threats with similar characteristics to show
how the system prevents duplicate alerts.
"""

import sys
import os
import django
import time

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'drishti_project.settings')
django.setup()

from api.models import TacticalUnit, Threat
from api.utils import generate_alerts, create_alert_key, get_alert_cache_stats, cleanup_expired_threats
from django.utils import timezone
from datetime import timedelta

def create_test_data():
    """Create test tactical unit and threats for testing."""
    # Create a test tactical unit (player)
    player_unit, created = TacticalUnit.objects.get_or_create(
        unit_id='S1-LEAD',
        defaults={
            'unit_type': 'LEAD',
            'latitude': 28.6139,  # Delhi coordinates
            'longitude': 77.2090,
            'status': 'OPERATIONAL'
        }
    )
    
    # Clear existing threats
    Threat.objects.all().delete()
    
    # Create test threats very close to player unit (within 2km)
    test_threats = [
        # Very close threats that should definitely trigger alerts (same city as player unit)
        {'type': 'TANK', 'lat': 19.3150, 'lon': 84.7942, 'confidence': 'HIGH'},  # ~10m away
        {'type': 'DRONE', 'lat': 19.3151, 'lon': 84.7943, 'confidence': 'HIGH'},  # ~20m away
        {'type': 'AIRPLANE', 'lat': 19.3152, 'lon': 84.7944, 'confidence': 'MEDIUM'},  # ~30m away
    ]
    
    threats = []
    for i, threat_data in enumerate(test_threats):
        threat = Threat.objects.create(
            threat_type=threat_data['type'],
            latitude=threat_data['lat'],
            longitude=threat_data['lon'],
            confidence=threat_data['confidence'],
            is_active=True
        )
        threats.append(threat)
        print(f"Created threat {i+1}: {threat}")
    
    return player_unit, threats

def test_duplicate_prevention():
    """Test the new threat-type-based alert system."""
    print("=" * 60)
    print("TESTING THREAT-TYPE-BASED ALERT SYSTEM")
    print("=" * 60)
    
    # Create test data
    player_unit, threats = create_test_data()
    
    # Initialize alert cache
    last_alert_cache = {}
    
    print(f"\nPlayer unit: {player_unit}")
    print(f"Number of threats: {len(threats)}")
    
    # Test 1: First round of alerts (should alert for each threat TYPE)
    print("\n" + "=" * 40)
    print("TEST 1: First round of alerts (should alert for each threat TYPE)")
    print("=" * 40)
    
    alerts, updated_cache = generate_alerts(player_unit, threats, last_alert_cache)
    last_alert_cache = updated_cache
    
    print(f"Generated {len(alerts)} alerts (should be 3 - one per threat type):")
    for i, alert in enumerate(alerts):
        print(f"  {i+1}. {alert['text']}")
        print(f"     Threat Type: {alert['threat_type']}, Alert Key: {alert['alert_key']}")
    
    cache_stats = get_alert_cache_stats(last_alert_cache)
    print(f"\nCache stats: {cache_stats}")
    
    # Test 2: Add more threats of same types (should NOT generate alerts)
    print("\n" + "=" * 40)
    print("TEST 2: Add more threats of same types (should NOT generate alerts)")
    print("=" * 40)
    
    # Add more threats of existing types (more tanks, drones, airplanes)
    Threat.objects.create(
        threat_type='TANK',
        latitude=19.3153,
        longitude=84.7945,
        confidence='HIGH',
        is_active=True
    )
    Threat.objects.create(
        threat_type='DRONE',
        latitude=19.3154,
        longitude=84.7946,
        confidence='MEDIUM',
        is_active=True
    )
    
    all_threats = list(Threat.objects.all())
    alerts2, updated_cache2 = generate_alerts(player_unit, all_threats, last_alert_cache)
    last_alert_cache = updated_cache2
    
    print(f"Generated {len(alerts2)} alerts (should be 0 - same threat types):")
    for i, alert in enumerate(alerts2):
        print(f"  {i+1}. {alert['text']}")
    
    # Test 3: Add new threat type (should generate alert)
    print("\n" + "=" * 40)
    print("TEST 3: Add new threat type (should generate alert)")
    print("=" * 40)
    
    # Add a new threat type
    new_threat = Threat.objects.create(
        threat_type='HELICOPTER',
        latitude=19.3155,
        longitude=84.7947,
        confidence='HIGH',
        is_active=True
    )
    
    all_threats = list(Threat.objects.all())
    alerts3, updated_cache3 = generate_alerts(player_unit, all_threats, last_alert_cache)
    last_alert_cache = updated_cache3
    
    print(f"Generated {len(alerts3)} alerts (should be 1 for new threat type):")
    for i, alert in enumerate(alerts3):
        print(f"  {i+1}. {alert['text']}")
        print(f"     Threat Type: {alert['threat_type']}")
    
    # Test 4: Test 10-second timeout for threats
    print("\n" + "=" * 40)
    print("TEST 4: Test 10-second timeout for threats")
    print("=" * 40)
    
    # Simulate time passage by setting last_detected to 15 seconds ago for some threats
    old_time = timezone.now() - timedelta(seconds=15)
    threats[0].last_detected = old_time
    threats[0].save()
    new_threat.last_detected = old_time
    new_threat.save()
    
    print(f"Set some threats last_detected to 15 seconds ago")
    
    # Run cleanup
    expired_count = cleanup_expired_threats()
    print(f"Cleanup deactivated {expired_count} threats")
    
    # Check which threats are now inactive
    for threat in all_threats:
        threat.refresh_from_db()
        print(f"Threat {threat.id} ({threat.threat_type}) is_active: {threat.is_active}")
    
    # Test alerts after cleanup
    alerts4, updated_cache4 = generate_alerts(player_unit, all_threats, last_alert_cache)
    last_alert_cache = updated_cache4
    
    print(f"Generated {len(alerts4)} alerts after timeout cleanup:")
    for i, alert in enumerate(alerts4):
        print(f"  {i+1}. {alert['text']}")
    
    # Test 5: Test re-alerting after 1 minute for same threat type
    print("\n" + "=" * 40)
    print("TEST 5: Test re-alerting after 1 minute for same threat type")
    print("=" * 40)
    
    # Simulate time passage by modifying cache timestamps
    current_time = time.time()
    for key in last_alert_cache:
        last_alert_cache[key] = current_time - 70  # 70 seconds ago
    
    alerts5, updated_cache5 = generate_alerts(player_unit, all_threats, last_alert_cache)
    last_alert_cache = updated_cache5
    
    print(f"Generated {len(alerts5)} alerts after 1+ minute (should re-alert for active threat types):")
    for i, alert in enumerate(alerts5):
        print(f"  {i+1}. {alert['text']}")
        print(f"     Threat Type: {alert['threat_type']}")
    
    final_cache_stats = get_alert_cache_stats(last_alert_cache)
    print(f"\nFinal cache stats: {final_cache_stats}")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    test_duplicate_prevention()

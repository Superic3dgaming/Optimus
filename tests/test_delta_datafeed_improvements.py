#!/usr/bin/env python3
"""
Test script to validate the improved error handling in DeltaDataFeed.

This script tests the improvements made to handle API endpoint failures,
configuration validation, and error reporting.
"""

import sys
import os
from unittest.mock import patch, MagicMock

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datafeeds.delta_datafeed import DeltaDataFeed

def test_explicit_option_product_id():
    """Test that explicit OPTIMUS_OPTION_PRODUCT_ID bypasses auto-selection."""
    print("Test 1: Explicit option product ID configuration")
    
    with patch.dict(os.environ, {
        'OPTIMUS_OPTION_PRODUCT_ID': '12345',
        'OPTIMUS_AUTO_SELECT': '1',
        'OPTIMUS_DEBUG': '1'
    }):
        feed = DeltaDataFeed(base_url="https://api.delta.exchange")
        result = feed.pick_option_instrument({})
        assert result == "12345", f"Expected '12345', got '{result}'"
        print("✓ Explicit product ID correctly bypasses auto-selection")

def test_auto_select_network_failure():
    """Test that auto-selection failure provides actionable error messages."""
    print("\nTest 2: Auto-selection with network failure")
    
    with patch.dict(os.environ, {
        'OPTIMUS_AUTO_SELECT': '1',
        'OPTIMUS_DEBUG': '1'
    }, clear=True):
        feed = DeltaDataFeed(base_url="https://invalid.api.endpoint")
        
        try:
            result = feed.pick_option_instrument({})
            assert False, "Expected RuntimeError but got result: " + str(result)
        except RuntimeError as e:
            error_msg = str(e)
            # Check that error message contains actionable guidance
            assert "OPTIMUS_OPTION_PRODUCT_ID" in error_msg, "Error should suggest setting OPTIMUS_OPTION_PRODUCT_ID"
            assert "OPTIMUS_OPTION_SYMBOL" in error_msg, "Error should suggest setting OPTIMUS_OPTION_SYMBOL"
            assert "network connectivity" in error_msg, "Error should mention network connectivity"
            print("✓ Auto-selection failure provides actionable error messages")

def test_no_auto_select_no_explicit():
    """Test error when auto-select is disabled and no explicit config is provided."""
    print("\nTest 3: No auto-select and no explicit configuration")
    
    with patch.dict(os.environ, {
        'OPTIMUS_AUTO_SELECT': '0',
    }, clear=True):
        feed = DeltaDataFeed(base_url="https://api.delta.exchange")
        
        try:
            result = feed.pick_option_instrument({})
            assert False, "Expected RuntimeError but got result: " + str(result)
        except RuntimeError as e:
            error_msg = str(e)
            assert "OPTIMUS_AUTO_SELECT=1" in error_msg, "Error should suggest enabling auto-select"
            assert "OPTIMUS_OPTION_PRODUCT_ID" in error_msg, "Error should suggest setting product ID"
            print("✓ Missing configuration provides helpful guidance")

def test_multiple_base_urls():
    """Test that multiple base URLs are properly configured."""
    print("\nTest 4: Multiple base URLs configuration")
    
    with patch.dict(os.environ, {
        'OPTIMUS_API_BASES': 'https://api1.example.com,https://api2.example.com',
        'OPTIMUS_DISABLE_DISCOVERY': '0'
    }):
        feed = DeltaDataFeed(base_url="https://primary.example.com")
        assert len(feed.base_urls) == 2, f"Expected 2 base URLs, got {len(feed.base_urls)}"
        assert "https://api1.example.com" in feed.base_urls, "First URL should be in base_urls"
        assert "https://api2.example.com" in feed.base_urls, "Second URL should be in base_urls"
        print("✓ Multiple base URLs are correctly configured")

def test_http_error_handling():
    """Test that HTTP errors are properly categorized and reported."""
    print("\nTest 5: HTTP error handling")
    
    # Mock the HTTP client to simulate different error responses
    feed = DeltaDataFeed(base_url="https://api.delta.exchange")
    
    # Test 404 error handling
    with patch.object(feed.http, 'get') as mock_get:
        mock_get.side_effect = Exception("404 Client Error: Not Found")
        
        try:
            feed._get("/test/path")
            assert False, "Expected RuntimeError for 404"
        except RuntimeError as e:
            assert "endpoint not found" in str(e).lower(), "404 should be reported as endpoint not found"
            assert "deprecated" in str(e).lower(), "404 error should mention deprecation"
            print("✓ 404 errors are properly categorized")

def test_debug_logging():
    """Test that debug logging works correctly."""
    print("\nTest 6: Debug logging")
    
    with patch.dict(os.environ, {'OPTIMUS_DEBUG': '1'}):
        feed = DeltaDataFeed(base_url="https://api.delta.exchange")
        assert feed._debug == True, "Debug should be enabled"
        print("✓ Debug logging is correctly enabled")
    
    with patch.dict(os.environ, {'OPTIMUS_DEBUG': '0'}):
        feed = DeltaDataFeed(base_url="https://api.delta.exchange")
        assert feed._debug == False, "Debug should be disabled"
        print("✓ Debug logging is correctly disabled")

def main():
    """Run all tests."""
    print("Testing improved DeltaDataFeed error handling...\n")
    
    try:
        test_explicit_option_product_id()
        test_auto_select_network_failure()
        test_no_auto_select_no_explicit()
        test_multiple_base_urls()
        test_http_error_handling()
        test_debug_logging()
        
        print(f"\n🎉 All tests passed! The improved error handling is working correctly.")
        return 0
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
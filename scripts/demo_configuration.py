#!/usr/bin/env python3
"""
Demo script showing how to use the improved DeltaDataFeed with proper configuration.

This script demonstrates the recommended way to configure and use DeltaDataFeed
after the error handling improvements.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def demo_explicit_configuration():
    """Demonstrate using explicit option product ID (recommended for production)."""
    print("=== Demo 1: Explicit Configuration (Recommended for Production) ===")
    print()
    
    print("# Set in your .env file:")
    print("OPTIMUS_OPTION_PRODUCT_ID=12345  # Replace with actual option product ID")
    print("OPTIMUS_PERP_PRODUCT_ID=3136     # Replace with actual perp product ID")
    print("OPTIMUS_API_BASE=https://api.delta.exchange")
    print()
    
    print("# This configuration:")
    print("✓ Bypasses API discovery (faster startup)")
    print("✓ Works even when product list API is unavailable")
    print("✓ Deterministic (always uses the same option)")
    print("✓ Production-ready")
    print()

def demo_auto_selection():
    """Demonstrate using auto-selection with proper fallback."""
    print("=== Demo 2: Auto-Selection with Fallback (Good for Development) ===")
    print()
    
    print("# Set in your .env file:")
    print("OPTIMUS_AUTO_SELECT=1")
    print("OPTIMUS_API_BASE=https://api.delta.exchange")
    print("OPTIMUS_DISABLE_DISCOVERY=0      # Enable endpoint discovery")
    print("OPTIMUS_OPTION_ROOT=ETH")
    print("OPTIMUS_OPTION_TYPE=both")
    print()
    
    print("# Benefits:")
    print("✓ Automatically selects nearest-expiry ATM options")
    print("✓ Adapts to market conditions")
    print("✓ Falls back gracefully on API failures")
    print("✓ Provides clear error messages")
    print()

def demo_multiple_apis():
    """Demonstrate using multiple API bases for redundancy."""
    print("=== Demo 3: Multiple API Bases for Redundancy ===")
    print()
    
    print("# Set in your .env file:")
    print("OPTIMUS_API_BASES=https://api.delta.exchange,https://testnet.delta.exchange")
    print("OPTIMUS_DISABLE_DISCOVERY=0")
    print()
    
    print("# How it works:")
    print("✓ Tries primary API first")
    print("✓ Falls back to secondary APIs if primary fails") 
    print("✓ Switches to working API automatically")
    print("✓ Provides detailed error reporting")
    print()

def demo_troubleshooting():
    """Show troubleshooting steps for common issues."""
    print("=== Demo 4: Troubleshooting Common Issues ===")
    print()
    
    print("Issue 1: 'Auto-selection failed' error")
    print("Solutions:")
    print("  1. Set OPTIMUS_OPTION_PRODUCT_ID=<valid_product_id>")
    print("  2. Check network connectivity")
    print("  3. Verify OPTIMUS_API_BASE is correct")
    print("  4. Enable debug: OPTIMUS_DEBUG=1")
    print()
    
    print("Issue 2: 'No option candles' error")
    print("Solutions:")
    print("  1. Verify the option exists and has trading history")
    print("  2. Try a different date range")
    print("  3. Check if the option symbol/product_id is correct")
    print("  4. Enable debug mode for detailed API logs")
    print()
    
    print("Issue 3: API endpoint not found (404)")
    print("Solutions:")
    print("  1. Check Delta Exchange API documentation for current endpoints")
    print("  2. Update OPTIMUS_API_PATH_PRODUCTS and OPTIMUS_API_PATH_CANDLES")
    print("  3. Try different API versions (/v3, /v2, /public)")
    print("  4. Set OPTIMUS_DISABLE_DISCOVERY=0 to enable endpoint discovery")
    print()

def demo_best_practices():
    """Show best practices for configuration."""
    print("=== Demo 5: Best Practices ===")
    print()
    
    print("For Production:")
    print("✓ Use explicit OPTIMUS_OPTION_PRODUCT_ID")
    print("✓ Set OPTIMUS_PERP_PRODUCT_ID")
    print("✓ Use stable API endpoints")
    print("✓ Set OPTIMUS_DISABLE_DISCOVERY=1 for consistency")
    print("✓ Monitor for API changes")
    print()
    
    print("For Development:")
    print("✓ Enable OPTIMUS_AUTO_SELECT=1")
    print("✓ Enable OPTIMUS_DEBUG=1")
    print("✓ Use OPTIMUS_DISABLE_DISCOVERY=0 for endpoint discovery")
    print("✓ Set fallback API bases")
    print()
    
    print("For Debugging:")
    print("✓ Always enable OPTIMUS_DEBUG=1")
    print("✓ Check logs for API request/response details")
    print("✓ Verify configuration with test scripts")
    print("✓ Test with known good product IDs first")
    print()

def main():
    """Run all demos."""
    print("DeltaDataFeed Configuration Guide")
    print("=" * 50)
    print()
    print("After the recent improvements, DeltaDataFeed now provides:")
    print("• Robust error handling with actionable messages")
    print("• Multiple API endpoint fallback")
    print("• Better configuration validation")
    print("• Comprehensive debugging information")
    print()
    
    demo_explicit_configuration()
    demo_auto_selection()
    demo_multiple_apis()
    demo_troubleshooting()
    demo_best_practices()
    
    print("=== Sample Working .env Configuration ===")
    print()
    print("# Production configuration")
    print("OPTIMUS_MODE=BACKTEST")
    print("OPTIMUS_API_BASE=https://api.delta.exchange")
    print("OPTIMUS_OPTION_PRODUCT_ID=12345  # Replace with real product ID")
    print("OPTIMUS_PERP_PRODUCT_ID=3136     # Replace with real product ID")
    print("OPTIMUS_CANDLES_SYMBOL_PARAM=product_id")
    print("OPTIMUS_UNDERLYING=ETHUSD")
    print()
    
    print("# Development configuration")
    print("OPTIMUS_MODE=BACKTEST")
    print("OPTIMUS_AUTO_SELECT=1")
    print("OPTIMUS_DEBUG=1")
    print("OPTIMUS_API_BASE=https://api.delta.exchange")
    print("OPTIMUS_DISABLE_DISCOVERY=0")
    print("OPTIMUS_OPTION_ROOT=ETH")
    print("OPTIMUS_OPTION_TYPE=both")
    print("OPTIMUS_UNDERLYING=ETHUSD")
    print("OPTIMUS_PERP_PRODUCT_ID=3136")
    print()

if __name__ == "__main__":
    main()
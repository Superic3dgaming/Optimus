# API Endpoint and Error Handling Improvements

This document describes the improvements made to the Optimus trading bot to fix API endpoint issues and improve error handling.

## Problem Statement

The original backtest mode failed with these issues:

1. **API endpoint access fails**: 404 errors from `https://api.delta.exchange/public/products?limit=10000`
2. **Unsafe fallback behavior**: Falls back to root symbol "ETH" which cannot be converted to product_id
3. **Poor error messages**: Generic errors without actionable guidance
4. **No endpoint discovery**: Single endpoint failure breaks the entire system

## Solutions Implemented

### 1. Robust API Endpoint Discovery

**Multiple Base URLs Support**
- Added `OPTIMUS_API_BASES` configuration for comma-separated fallback URLs
- Automatic failover between API bases when one becomes unavailable
- Smart base URL switching to use working endpoints

**Multiple Endpoint Paths**
- Try multiple API versions: `/v3/public/products`, `/v2/public/products`, `/public/products`
- Configurable via `OPTIMUS_API_PATH_PRODUCTS` and `OPTIMUS_API_PATH_CANDLES`
- Automatic discovery of working endpoints when `OPTIMUS_DISABLE_DISCOVERY=0`

### 2. Enhanced Error Handling

**Specific HTTP Error Classification**
- 404 errors → "API endpoint not found, may be deprecated"
- 401/403 errors → "API access denied, check credentials"
- 429 errors → "Rate limited, reduce request frequency"
- 5xx errors → "Server error, try again later"

**Actionable Error Messages**
- Clear guidance on what to do when errors occur
- Suggestions for configuration changes
- References to documentation and troubleshooting steps

### 3. Improved Configuration Validation

**Removed Unsafe Fallbacks**
- No longer falls back to root symbol ("ETH") when endpoint expects product_id
- Validates configuration compatibility before making API calls
- Prevents runtime crashes from misconfiguration

**Better Configuration Options**
- Explicit `OPTIMUS_OPTION_PRODUCT_ID` for production use
- Auto-selection with `OPTIMUS_AUTO_SELECT=1` for development
- Clear error messages when neither is properly configured

### 4. Comprehensive Debugging Support

**Debug Logging**
- Enable with `OPTIMUS_DEBUG=1`
- Shows all API requests and responses
- Detailed error tracing for troubleshooting

**Better Logging Output**
- Clear indication of which endpoints are being tried
- Success/failure status for each attempt
- Helpful warnings and informational messages

## Configuration Examples

### Production Configuration (Recommended)
```bash
# Explicit configuration - fastest and most reliable
OPTIMUS_MODE=BACKTEST
OPTIMUS_API_BASE=https://api.delta.exchange
OPTIMUS_OPTION_PRODUCT_ID=12345  # Replace with actual option product ID
OPTIMUS_PERP_PRODUCT_ID=3136     # Replace with actual perp product ID
OPTIMUS_CANDLES_SYMBOL_PARAM=product_id
OPTIMUS_UNDERLYING=ETHUSD
```

### Development Configuration
```bash
# Auto-selection with fallback
OPTIMUS_MODE=BACKTEST
OPTIMUS_AUTO_SELECT=1
OPTIMUS_DEBUG=1
OPTIMUS_API_BASE=https://api.delta.exchange
OPTIMUS_DISABLE_DISCOVERY=0
OPTIMUS_OPTION_ROOT=ETH
OPTIMUS_OPTION_TYPE=both
OPTIMUS_UNDERLYING=ETHUSD
OPTIMUS_PERP_PRODUCT_ID=3136
```

### Redundant API Configuration
```bash
# Multiple API bases for high availability
OPTIMUS_API_BASES=https://api.delta.exchange,https://testnet.delta.exchange
OPTIMUS_DISABLE_DISCOVERY=0
OPTIMUS_AUTO_SELECT=1
```

## Testing and Validation

### Automated Tests
Run the test suite to validate the improvements:
```bash
python tests/test_delta_datafeed_improvements.py
```

Tests cover:
- Explicit configuration bypassing auto-selection
- Network failure handling with actionable errors
- Configuration validation
- Multiple base URL support
- HTTP error categorization
- Debug logging functionality

### Manual Testing
Use the demo script to understand configuration options:
```bash
python scripts/demo_configuration.py
```

## Migration Guide

### If you currently use auto-selection
1. Keep `OPTIMUS_AUTO_SELECT=1`
2. Add `OPTIMUS_DISABLE_DISCOVERY=0` to enable endpoint discovery
3. Consider adding `OPTIMUS_API_BASES` for redundancy
4. Enable `OPTIMUS_DEBUG=1` during migration

### If you use explicit configuration
1. Ensure `OPTIMUS_OPTION_PRODUCT_ID` is set to a valid product ID
2. Set `OPTIMUS_PERP_PRODUCT_ID` if using `OPTIMUS_CANDLES_SYMBOL_PARAM=product_id`
3. Verify your API base URL is correct
4. Consider adding fallback URLs via `OPTIMUS_API_BASES`

### Common Migration Issues

**Error: "Auto-selection failed"**
- Solution: Set `OPTIMUS_OPTION_PRODUCT_ID` to bypass auto-selection
- Or fix network connectivity and API base URL

**Error: "No option candles found"**
- Solution: Verify the product ID exists and has trading history
- Try a different date range or option
- Enable debug mode to see API responses

**Error: "API endpoint not found"**
- Solution: Update to current Delta Exchange API endpoints
- Enable endpoint discovery with `OPTIMUS_DISABLE_DISCOVERY=0`
- Check Delta Exchange API documentation

## Benefits

1. **Reliability**: Graceful fallback when APIs fail
2. **Debuggability**: Clear error messages and debug logging
3. **Maintainability**: Easy to update API endpoints and configuration
4. **User Experience**: Actionable guidance instead of cryptic errors
5. **Production Ready**: Explicit configuration for stable operation

## Future Considerations

1. **API Monitoring**: Consider adding health checks for API endpoints
2. **Configuration UI**: Web interface for easier configuration management
3. **Automated Testing**: Integration tests with real API endpoints
4. **Documentation**: Keep API endpoint documentation updated
5. **Alerting**: Notify operators when APIs become unavailable
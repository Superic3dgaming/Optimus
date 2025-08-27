"""
Configuration validation and startup checks for Optimus.
"""
import os
from typing import List, Dict, Any, Tuple
from core.logger import get_logger

logger = get_logger()

# Required environment variables and their descriptions
REQUIRED_ENV_VARS = {
    "OPTIMUS_MODE": "Trading mode: BACKTEST, PAPER, or LIVE",
}

# Optional environment variables with defaults and descriptions
OPTIONAL_ENV_VARS = {
    "OPTIMUS_DEBUG": "Enable debug logging (1, true, yes)",
    "OPTIMUS_API_BASE": "Base URL for Delta Exchange API",
    "OPTIMUS_API_PATH_CANDLES": "API path for candles endpoint",
    "OPTIMUS_API_PATH_PRODUCTS": "API path for products endpoint",
    "OPTIMUS_CANDLES_INTERVAL_PARAM": "Parameter name for interval in candles API",
    "OPTIMUS_CANDLES_SYMBOL_PARAM": "Parameter name for symbol in candles API (product_id or symbol)",
    "OPTIMUS_CANDLES_START_PARAM": "Parameter name for start time in candles API",
    "OPTIMUS_CANDLES_END_PARAM": "Parameter name for end time in candles API",
    "OPTIMUS_UNDERLYING": "Underlying symbol for perpetual contracts",
    "OPTIMUS_OPTION_ROOT": "Root symbol for options",
    "OPTIMUS_OPTION_TYPE": "Preferred option type: call, put, or both",
    "OPTIMUS_PERP_PRODUCT_ID": "Product ID for perpetual contract (required if using product_id param)",
    "OPTIMUS_OPTION_PRODUCT_ID": "Explicit option product ID (bypasses auto-selection)",
    "OPTIMUS_OPTION_SYMBOL": "Explicit option symbol (bypasses auto-selection)",
    "OPTIMUS_DISABLE_DISCOVERY": "Disable API endpoint discovery",
    "OPTIMUS_AUTO_SELECT": "Enable automatic option selection",
    "OPTIMUS_START_EQUITY": "Starting equity for backtesting",
}

def validate_env_config() -> Tuple[List[str], List[str]]:
    """
    Validate environment configuration.
    Returns: (errors, warnings) - lists of error/warning messages
    """
    errors = []
    warnings = []
    
    # Check required variables
    for var, description in REQUIRED_ENV_VARS.items():
        value = os.getenv(var)
        if not value:
            errors.append(f"Missing required environment variable: {var} ({description})")
    
    # Validate OPTIMUS_MODE if present
    mode = os.getenv("OPTIMUS_MODE", "").upper()
    if mode and mode not in ["BACKTEST", "PAPER", "LIVE"]:
        errors.append(f"Invalid OPTIMUS_MODE: {mode}. Must be BACKTEST, PAPER, or LIVE")
    
    # Check symbol parameter configuration
    symbol_param = os.getenv("OPTIMUS_CANDLES_SYMBOL_PARAM", "product_id")
    if symbol_param == "product_id":
        perp_pid = os.getenv("OPTIMUS_PERP_PRODUCT_ID")
        if not perp_pid:
            warnings.append(
                "OPTIMUS_CANDLES_SYMBOL_PARAM=product_id but OPTIMUS_PERP_PRODUCT_ID is not set. "
                "This may cause issues when fetching underlying prices."
            )
        elif not perp_pid.isdigit():
            errors.append(f"OPTIMUS_PERP_PRODUCT_ID must be numeric, got: {perp_pid}")
    
    # Check option configuration
    auto_select = os.getenv("OPTIMUS_AUTO_SELECT", "1").lower() in ("1", "true", "yes")
    explicit_opt_pid = os.getenv("OPTIMUS_OPTION_PRODUCT_ID")
    explicit_opt_symbol = os.getenv("OPTIMUS_OPTION_SYMBOL")
    
    if not auto_select and not explicit_opt_pid and not explicit_opt_symbol:
        warnings.append(
            "OPTIMUS_AUTO_SELECT is disabled and no explicit option product ID or symbol is set. "
            "Option data fetching may fail."
        )
    
    # Check numeric values
    start_equity = os.getenv("OPTIMUS_START_EQUITY")
    if start_equity:
        try:
            float(start_equity)
        except ValueError:
            errors.append(f"OPTIMUS_START_EQUITY must be numeric, got: {start_equity}")
    
    return errors, warnings

def log_config_overrides() -> None:
    """
    Log all configuration values for transparency.
    """
    logger.info("=== Optimus Configuration ===")
    
    # Log all environment variables used by Optimus
    all_vars = {**REQUIRED_ENV_VARS, **OPTIONAL_ENV_VARS}
    
    for var, description in all_vars.items():
        value = os.getenv(var)
        if value:
            # Mask sensitive values if any (none currently)
            masked_value = value
            logger.info(f"{var}={masked_value} ({description})")
        else:
            logger.info(f"{var}=<not set> ({description})")
    
    logger.info("=== End Configuration ===")

def validate_startup() -> bool:
    """
    Perform startup validation and logging.
    Returns True if all critical checks pass, False otherwise.
    """
    from scripts.verify_structure import main as verify_structure
    
    logger.info("Starting Optimus configuration validation...")
    
    # First check repository structure
    try:
        verify_structure()
        logger.info("Repository structure validation passed")
    except SystemExit as e:
        if e.code != 0:
            logger.error("Repository structure validation failed")
            return False
    except Exception as e:
        logger.error(f"Repository structure validation error: {e}")
        return False
    
    # Log configuration
    log_config_overrides()
    
    # Validate environment configuration
    errors, warnings = validate_env_config()
    
    # Log warnings
    for warning in warnings:
        logger.warning(warning)
    
    # Log errors and return status
    if errors:
        logger.error(f"Configuration validation failed with {len(errors)} error(s):")
        for error in errors:
            logger.error(f"  - {error}")
        
        logger.info("\nTo fix these issues:")
        logger.info("1. Copy .env.example to .env if you haven't already")
        logger.info("2. Edit .env to set the required values")
        logger.info("3. Check the documentation for more details")
        return False
    else:
        logger.info(f"Configuration validation passed (with {len(warnings)} warning(s))")
        return True
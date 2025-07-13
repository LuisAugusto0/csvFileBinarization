"""
Utilities package for CSV file binarization and processing
"""

# Import all utilities for easy access
from .string_utils import (
    normalize_string,
    arrayTest,
    arrayStringContainsTest,
    arrayStringEqualsTest,
    arrayStringTestNot
)

from .ui_utils import (
    scan_input,
    interactive_print,
    display_threshold_types,
    get_column_from_input,
    display_main_menu,
    display_column_removal_menu
)

from .df_manipulation import (
    binarize_column,
    remove_rows_by_match,
    list_column_unique_values
)

from .conversions import SlfConversion

__all__ = [
    # String utilities
    'normalize_string',
    'arrayTest',
    'arrayStringContainsTest',
    'arrayStringEqualsTest',
    'arrayStringTestNot',
    
    # UI utilities
    'scan_input',
    'interactive_print',
    'display_threshold_types',
    'get_column_from_input',
    'display_main_menu',
    'display_column_removal_menu',

    # Core operation
    'binarize_column',
    'remove_rows_by_match',
    'list_column_unique_values',
    
    # Conversions
    'SlfConversion'
]
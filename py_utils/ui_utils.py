"""
User interface utility functions for interactive prompts and displays
"""
from .string_utils import normalize_string

def scan_input(prompt, is_interactive=True):
    """Scan input from the user with a prompt"""
    if is_interactive:
        return normalize_string(input(prompt))
    else:
        # In non-interactive mode, read from standard input
        return normalize_string(input())


def interactive_print(*print_args, is_interactive=True, **print_kwargs):
    """Print only if in interactive mode"""
    if is_interactive:
        print(*print_args, **print_kwargs)


def get_column_from_input(input_str, current_columns):
    """
    Helper function to get column from input string, which can be either an index or column name
    
    Args:
        input_str: User input string
        current_columns: List of available columns
        
    Returns:
        Column name if found, None otherwise
    """
    # Try to parse as index first
    try:
        index = int(input_str)
        if 0 <= index < len(current_columns):
            return current_columns[index]
        else:
            print(f"Invalid index: {index}. Must be between 0 and {len(current_columns)-1}")
            return None
    except ValueError:
        # Not an index, check if it's a valid column name
        if input_str in current_columns:
            return input_str
        else:
            print(f"Column '{input_str}' not found in the DataFrame")
            return None

def display_threshold_types():
    """Helper function to display available threshold types"""
    print("\n=== Available Threshold Types ===")
    print("- 'superior': Mark when value < threshold")
    print("- 'inferior': Mark when value > threshold")
    print("- 'superior_inferior': Mark when threshold[1] < value < threshold[0]")
    print("- 'equals': Mark when value == threshold")
    print("- 'not_equals': Mark when value == threshold")
    print("- 'string_contains': Mark when string contains threshold")
    print("- 'string_not_contains': Mark when string doesn't contain threshold")
    print("- 'string_equals': Mark when string == threshold (for multiple values, if all are equal)")
    print("- 'string_not_equals': Mark when string != threshold (for multiple values, if all are different)")

def display_main_menu():
    """Display the main processing menu options"""
    print("\n===== Main Menu =====")
    print("Available options:")
    print("- 'drop': Select columns to drop from the dataset")
    print("- 'bin': Binarize columns based on thresholds")
    print("- 'remove': Remove specific rows based on values")
    print("- 'export': Export the processed file as CSV and SLF")
    print("- 'info': Display current DataFrame information")
    print("- 'exit': Exit without saving")
    print("- 'h': Show this help menu")
    print("=====================")

def display_column_removal_menu():
        """Helper function to display menu options"""
        interactive_print("\n=== Column Removal Options ===")
        interactive_print("- Enter a single index or column name (e.g. '5') to mark a column for removal")
        interactive_print("- Enter a index or column name range (e.g. '5-10') to mark multiple columns for removal")
        interactive_print("- Enter 'u' to access the undo menu")
        interactive_print("- Enter 'l' to list all columns again")
        interactive_print("- Enter 'r' to display  only columns marked for removal")
        interactive_print("- Enter 'h' to this menu again")
        interactive_print("- Enter 'done' to finish selection")
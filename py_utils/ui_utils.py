"""
User interface utility functions for interactive prompts and displays
"""
from .string_utils import normalize_string

def scan_input(prompt, is_interactive=True):
    """Scan input from the user with a prompt"""
    user_input = ""
    if is_interactive:
        user_input = input(prompt)
    else:
        # In non-interactive mode, read from standard input
        user_input = input()
    while(user_input == ""):
            user_input = input()
    return normalize_string(user_input)


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

def display_threshold_types(is_interactive=True):
    """Helper function to display available threshold types"""
    interactive_print(
        "\n=== Available Threshold Types ===\n"
        "- 'superior': Mark when value < threshold\n"
        "- 'inferior': Mark when value > threshold\n"
        "- 'superior_inferior': Mark when threshold[1] < value < threshold[0]\n"
        "- 'equals': Mark when value == threshold\n"
        "- 'not_equals': Mark when value != threshold\n"
        "- 'string_contains': Mark when string contains threshold\n"
        "- 'string_not_contains': Mark when string doesn't contain threshold\n"
        "- 'string_equals': Mark when string == threshold (for multiple values, if all are equal)\n"
        "- 'string_not_equals': Mark when string != threshold (for multiple values, if all are different)",
        is_interactive=is_interactive
    )

def display_main_menu(is_interactive=True):
    """Display the main processing menu options"""
    interactive_print(
        "\n===== Main Menu =====\n"
        "Available options:\n"
        "- 'drop': Select columns to drop from the dataset\n"
        "- 'bin': Binarize columns based on thresholds\n"
        "- 'remove': Remove specific rows based on values\n"
        "- 'remove_null': Remove instances that contains null values from all the database\n"
        "- 'export': Export the processed file as CSV and SLF\n"
        "- 'info': Display current DataFrame information\n"
        "- 'exit': Exit without saving\n"
        "- 'h': Show this help menu\n"
        "=====================",
        is_interactive=is_interactive
    )

def display_column_removal_menu(is_interactive=True):
    """Helper function to display menu options"""
    interactive_print(
        "\n=== Column Removal Options ===\n"
        "- Enter a single index or column name (e.g. '5') to mark a column for removal\n"
        "- Enter a index or column name range (e.g. '5-10') to mark multiple columns for removal\n"
        "- Enter 'u' to access the undo menu\n"
        "- Enter 'l' to list all columns again\n"
        "- Enter 'r' to display only columns marked for removal\n"
        "- Enter 'h' to this menu again\n"
        "- Enter 'done' to finish selection",
        is_interactive=is_interactive
    )
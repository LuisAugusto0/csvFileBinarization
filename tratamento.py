import csv
import pandas as pd
import numpy as np
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
import argparse
import re
import os
import traceback

def interactive_print(*print_args, **print_kwargs):
    if is_interactive:
        print(*print_args, **print_kwargs)

def normalize_string(name):
    """Normalize a column name by removing whitespace and replacing special characters (excluding hyphen and comma) with underscores"""
    name = str(name).strip().lower()  # Convert to string, strip whitespace, and lowercase
    name = re.sub(r'[^\w\s,-]', '_', name)  # Replace non-word/non-space/non-hyphen/non-comma chars with _
    name = re.sub(r'\s+', '_', name)      # Replace spaces with _
    name = re.sub(r'_+', '_', name)        # Collapse multiple _ into one
    return name

def scan_input(prompt):
    """Scan input from the user with a prompt"""
    if is_interactive:
        return normalize_string(input(prompt))
    else:
        # In non-interactive mode, read from standard input
        return normalize_string(input())

def arrayTest(array, value):
    """
    Tests if a value is in the array
    
    Args:
        array: Array to be tested
        value: Value (number) to be tested
        
    Returns:
        bool: True if the value is in the array, False otherwise
    """
    for i in range(len(array)):
        if array[i] == value:
            return True
    return False

def arrayStringTest(array, string_methods):
    """
    Tests if any of the values in the array is contained in the given string series
    
    Args:
        array: Array of strings to check for
        string_methods: The string accessor (Series.str) to check against
        
    Returns:
        Series: Boolean Series with True where any value in array is found
    """
    # Create a mask that starts with all False
    result = pd.Series(False, index=string_methods._parent.index)
    
    # For each threshold, update the mask where the strings contain that threshold
    for threshold in array:
        result = result | string_methods.contains(threshold, na=False)
    
    return result

def arrayStringTestNot(array, string_methods):
    """
    Tests if none of the values in the array are contained in the given string
    
    Args:
        array: Array of strings to check for
        string_methods: The string accessor (Series.str) to check against
        
    Returns:
        Series: Boolean Series with True where no value in array is found
    """
    # Create a mask that starts with all True
    result = pd.Series(True, index=string_methods._parent.index)
    
    # For each threshold, update the mask to exclude strings containing the threshold
    for threshold in array:
        result = result & ~string_methods.contains(threshold, na=False)
    
    return result
    
def binarizeColumn(df, column_names, new_column_name, threshold, threshold_type):
    """
    Binarizes one or multiple columns in the DataFrame based on a threshold.
    
    Args:
        df: DataFrame to be modified
        column_names: Name(s) of column(s) to be binarized (string or list of strings)
        new_column_name: Name of the column after binarization
        threshold: Threshold for binarization
        threshold_type: Type of threshold ('superior', 'inferior', 'superior_inferior', 
                      'equals', 'not_equals', 'string_equals' or 'string_not_equals')
        
    Returns:
        pandas.DataFrame: Modified DataFrame
    """
    # Convert single column name to list for consistent handling
    if isinstance(column_names, str):
        column_names = [column_names]
    
    # Verify that at least one column exists in the DataFrame
    valid_columns = [col for col in column_names if col in df.columns]

    # Print warning for the columns that do not exist
    if len(valid_columns) != len(column_names):
        missing_columns = set(column_names) - set(valid_columns)
        # Warnings should always be displayed, not just in interactive mode
        print("=== Warning ===")
        print(f"The following columns do not exist in the DataFrame:\n{'\n'.join(missing_columns)}")
        print("Proceeding with the existing columns.")
        print("=== End of Warning ===\n")
    
    if not valid_columns:
        print(f"Warning: None of the specified columns {column_names} exist in the DataFrame")
        return df
    
    interactive_print(f"Performing binarization on columns: {', '.join(valid_columns)}")

    # Create a temporary working column if multiple columns are provided
    if len(valid_columns) > 1:
        # Choose appropriate combination based on threshold_type
        if threshold_type in ('superior', 'not_Equals'):
            # Use any (logical OR) - if any column meets condition
            df['_temp_combined'] = df[valid_columns].min(axis=1)
        elif threshold_type in ('inferior', 'equals'):
            # Use all (logical AND) - all columns must meet condition
            df['_temp_combined'] = df[valid_columns].max(axis=1)
        # elif threshold_type == 'string_equals':
        #     # Create concatenated string column for text search
        #     df['_temp_combined'] = df[valid_columns].astype(str).agg('/'.join, axis=1)
        #     print(f"Temporary column created for string search: {df['_temp_combined']}")
        # elif threshold_type == 'string_not_Equals':
        #     # Create concatenated string column for text search
        #     df['_temp_combined'] = df[valid_columns].astype(str).agg('/'.join, axis=1)
        elif threshold_type == 'superior_inferior':
            # For range checks, use the mean of each row
            df['_temp_combined'] = df[valid_columns].mean(axis=1)
        else:
            print(f"Warning: Threshold type '{threshold_type}' not supported for multiple columns")
            return df
        
        # Use the temporary column for the binarization
        working_column = '_temp_combined'
    elif threshold_type == 'string_equals' or threshold_type == 'string_not_equals':
        # Create concatenated string column for text search
        df['_temp_combined'] = df[valid_columns].astype(str).apply(lambda col: col.map(normalize_string)).agg(lambda x: '/' + '/'.join(x) + '/', axis=1)
        working_column = '_temp_combined'
        print(f"Temporary column created for string search: {df['_temp_combined'].value_counts()}")
    else:
        # Use the single valid column directly
        working_column = valid_columns[0]
    
    # Perform the binarization based on threshold_type
    if threshold_type == 'superior':
        df[new_column_name] = np.where(df[working_column] < threshold, "1", "0")
    elif threshold_type == 'inferior':
        df[new_column_name] = np.where(df[working_column] > threshold, "1", "0")
    elif threshold_type == 'superior_inferior':
        df[new_column_name] = np.where((df[working_column] < threshold[0]) & (df[working_column] > threshold[1]), "1", "0")
    elif threshold_type == 'equals':
        if isinstance(threshold, (int, float)):
            df[new_column_name] = np.where(df[working_column] == threshold, "1", "0")
        else:
            df[new_column_name] = np.where(arrayTest(df[working_column], threshold), "1", "0")
    elif threshold_type == 'not_equals':
        if isinstance(threshold, (int, float)):
            df[new_column_name] = np.where(df[working_column] != threshold, "1", "0")
        else:
            df[new_column_name] = np.where(not arrayTest(df[working_column], threshold), "1", "0")
    elif threshold_type == 'string_equals':
        if not "," in threshold:
            threshold = f"/{threshold}/"
            df[new_column_name] = np.where(df[working_column].str.contains(threshold, na=False), "1", "0")
        else:
            threshold = threshold.split(",")
            threshold = [f"/{item.strip()}/" for item in threshold]
            # Apply the arrayStringTest function to get a boolean Series
            df[new_column_name] = np.where(arrayStringTest(threshold, df[working_column].str), "1", "0")
    elif threshold_type == 'string_not_equals':
        if not "," in threshold:
            threshold = f"/{threshold}/"
            df[new_column_name] = np.where(df[working_column].str.contains(threshold, na=False), "0", "1")
        else:
            threshold = threshold.split(",")
            threshold = [f"/{item.strip()}/" for item in threshold]
            # Apply the arrayStringTestNot function to get a boolean Series
            df[new_column_name] = np.where(arrayStringTestNot(threshold, df[working_column].str), "1", "0")
    else:
        print(f"Invalid threshold type: {threshold}. Use 'superior', 'inferior', etc.")
        return df
    
    # Clean up temporary column if it was created
    if len(valid_columns) > 1 and '_temp_combined' in df.columns:
        df = df.drop('_temp_combined', axis=1)
    
    print(f"{df[new_column_name].value_counts()}\n")
    
    return df

def readColumnsToDrop(df):
    """
    Interactive function to select columns for removal with undo capability
    
    Args:
        df (pandas.DataFrame): The DataFrame containing columns
        
    Returns:
        list: List of column names to be dropped
    """
    columns_to_drop = []
    removed_columns_history = []  # Stack to track removed columns for undo
    df_columns = list(df.columns)  # Original column list
    
    # First find duplicate columns
    interactive_print("\n===== Columns to drop menu =====")
    
    def display_columns(cols_list, to_drop):
        """Helper function to display columns with their indices"""
        interactive_print("\n=== Available Columns ===")
        for i, col in enumerate(cols_list):
            status = ""
            if col in to_drop:
                status = " [MARKED FOR REMOVAL]"
            interactive_print(f"[{i}] {col}{status}")
    
    def display_menu():
        """Helper function to display menu options"""
        interactive_print("\n=== Column Removal Options ===")
        interactive_print("- Enter a single index or column name (e.g. '5') to mark a column for removal")
        interactive_print("- Enter a index or column name range (e.g. '5-10') to mark multiple columns for removal")
        interactive_print("- Enter 'u' to access the undo menu")
        interactive_print("- Enter 'l' to list all columns again")
        interactive_print("- Enter 'r' to display  only columns marked for removal")
        interactive_print("- Enter 'h' to this menu again")
        interactive_print("- Enter 'done' to finish selection")
    
    display_columns(df_columns, columns_to_drop)
    display_menu()
    
    while True:
        user_input = scan_input("\nEnter command: ")
        
        if user_input == 'done':
            break
        elif user_input == 'l':
            display_columns(df_columns, columns_to_drop)
        elif user_input == 'r':
            if columns_to_drop:
                interactive_print("\n=== Columns Marked for Removal ===")
                for i, col in enumerate(columns_to_drop):
                    reason = ""
                    for c, r in removed_columns_history:
                        if c == col:
                            reason = f" - Reason: {r}"
                            break
                    interactive_print(f"{i}. {col}{reason}")
            else:
                interactive_print("No columns are currently marked for removal.")
        elif user_input == 'u':
            if not removed_columns_history:
                interactive_print("No actions to undo!")
                continue
            
            interactive_print("Recently removed columns:")
            for i, (col, reason) in enumerate(removed_columns_history):
                interactive_print(f"{i}. {col} - {reason}")
            interactive_print("\n=== Undo Menu ===")   
            undo_input = scan_input("Enter index or range to restore (e.g., '2' or '2-4', or 'back' to return): ")
            while undo_input != 'back':
                try:
                    if '-' in undo_input:
                        # Handle range input
                        start_idx, end_idx = map(int, undo_input.split('-'))
                        if 0 <= start_idx <= end_idx < len(removed_columns_history):
                            # Create a list of items to restore (in reverse order)
                            items_to_restore = [removed_columns_history[i] for i in range(start_idx, end_idx + 1)]
                            
                            # Remove these items from history (starting from the end to avoid index shifting)
                            for i in range(end_idx, start_idx - 1, -1):
                                removed_columns_history.pop(i)
                            
                            # Now restore all items
                            for col_to_restore, reason in items_to_restore:
                                if col_to_restore in columns_to_drop:
                                    columns_to_drop.remove(col_to_restore)
                                    interactive_print(f"Restored column: {col_to_restore}")
                                else:
                                    interactive_print(f"Warning: Column {col_to_restore} was not in removal list")
                        else:
                            interactive_print("Invalid range! Please enter valid indices.")
                    else:
                        # Handle single index input
                        undo_index = int(undo_input)
                        if 0 <= undo_index < len(removed_columns_history):
                            col_to_restore, _ = removed_columns_history.pop(undo_index)
                            if col_to_restore in columns_to_drop:
                                columns_to_drop.remove(col_to_restore)
                                interactive_print(f"Restored column: {col_to_restore}")
                            else:
                                interactive_print(f"Warning: Column {col_to_restore} was not in removal list")
                        else:
                            interactive_print("Invalid index!")
                except ValueError:
                    interactive_print("Invalid input! Please enter a valid index or range.")
                if(len(removed_columns_history) == 0):
                    interactive_print("No actions to undo!")
                    break
                interactive_print("\nRecently removed columns:")
                for i, (col, reason) in enumerate(removed_columns_history):
                    interactive_print(f"{i}. {col} - {reason}")
                undo_input = scan_input("Enter index or range to restore (e.g., '2' or '2-4', or 'back' to return): ")
        elif user_input == 'h':
            display_menu()
        else:
            try:
                # Parse range input
                if '-' in user_input:
                    start, end = map(int, user_input.split('-'))
                    if (isinstance(start, str)) and (not start.isdigit()):
                        start = df_columns.index(start)
                    if (isinstance(end, str)) and (not end.isdigit()):
                        end = df_columns.index(end)
                    # Ensure valid range
                    if 0 <= start <= end < len(df_columns):
                        # Add columns to drop list with reason
                        for i in range(start, end + 1):
                            col = df_columns[i]
                            if col not in columns_to_drop:
                                columns_to_drop.append(col)
                                removed_columns_history.append((col, f"Manual selection (range {start}-{end})"))
                        interactive_print(f"Marked columns {start} to {end} for removal")
                    else:
                        interactive_print("Invalid range! Please enter valid column indices.")
                else:
                    # Single column case
                    if  (isinstance(user_input, str)) and (not user_input.isdigit()):
                        user_input = df_columns.index(user_input)
                    index = int(user_input)
                    if 0 <= index < len(df_columns):
                        col = df_columns[index]
                        if col not in columns_to_drop:
                            columns_to_drop.append(col)
                            removed_columns_history.append((col, f"Manual selection (index {index})"))
                            interactive_print(f"Marked column '{col}' for removal")
                        else:
                            interactive_print(f"Column '{col}' is already marked for removal")
                    else:
                        interactive_print("Invalid index! Please enter a valid column index.")
            except ValueError:
                interactive_print("Invalid input! Please use the format shown in the menu.")
                traceback.print_exc()

    
    # Summary - always displayed
    print(f"\n=== Summary: {len(columns_to_drop)} columns selected for removal ===")
    if columns_to_drop:
        for col in columns_to_drop:
            print(f"- {col}")
    print("================================================\n")
    return columns_to_drop

def binarizeColumnsMenu(df):
    """
    Interactive function to binarize columns with options for configuration
    
    Args:
        df (pandas.DataFrame): The DataFrame containing columns to binarize
        
    Returns:
        pandas.DataFrame: The DataFrame with binarized columns added
    """
    df_result = df.copy()
    df_columns = list(df.columns)  # Get original column list
    binarized_columns_history = []  # Track binarized columns for display
    columns_to_drop = []  # Track columns that will be dropped at the end
    replaced_columns = []  # Track columns that have been replaced (should not be auto-dropped)
    auto_remove_base_columns = True  # Flag to control auto removal at the end
    auto_replaced_columns = set()  # Track columns modified by the 'a' command
    
    interactive_print("\n===== Column Binarization Menu =====")
    
    def display_columns(cols_list, binarized):
        """Helper function to display columns with their indices"""
        interactive_print("\n=== Available Columns ===")
        for i, col in enumerate(cols_list):
            status = ""
            if any(col == src_col for src_col, _, _, _, _ in binarized):
                if isinstance(src_col, list):
                    if col in src_col:
                        status = " [BASE FOR BINARIZATION]"
                else:
                    status = " [BASE FOR BINARIZATION]"
            
            if col in [new_col for _, new_col, _, _, _ in binarized]:
                status = " [BINARIZED COLUMN]"
                
            if col in columns_to_drop:
                status += " [MARKED FOR REMOVAL]"
                
            interactive_print(f"[{i}] {col}{status}")
    
    def display_threshold_types():
        """Helper function to display available threshold types"""
        interactive_print("\n=== Available Threshold Types ===")
        interactive_print("- 'superior': Mark when value < threshold")
        interactive_print("- 'inferior': Mark when value > threshold")
        interactive_print("- 'superior_inferior': Mark when threshold[1] < value < threshold[0]")
        interactive_print("- 'equals': Mark when value == threshold")
        interactive_print("- 'not_equals': Mark when value == threshold")
        interactive_print("- 'string_equals': Mark when string contains threshold")
        interactive_print("- 'string_not_equals': Mark when string doesn't contain threshold")
    
    def display_menu():
        """Helper function to display menu options"""
        interactive_print("\n=== Column Binarization Options ===")
        interactive_print("- Enter a single index or column name (e.g. '5') to binarize a column")
        interactive_print("- Enter a comma-separated list (e.g. '1,3,name1,5') to binarize multiple columns")
        interactive_print("- Enter 'a' to automatically replace values with '1'/''0'' across columns")
        interactive_print("- Enter 'r' to remove a binarized column")
        interactive_print("- Enter 'l' to list all columns")
        interactive_print("- Enter 'h' to show this help menu")
        interactive_print("- Enter 's' to show binarized columns summary")
        interactive_print("- Enter 'k' to toggle auto-removal of base columns")
        interactive_print("- Enter 'done' to finish binarization")
        
        # Show current auto-removal status
        status = "ENABLED" if auto_remove_base_columns else "DISABLED"
        interactive_print(f"Auto-removal of base columns: {status}")
    
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
                interactive_print(f"Invalid index: {index}. Must be between 0 and {len(current_columns)-1}")
                return None
        except ValueError:
            # Not an index, check if it's a valid column name
            if input_str in current_columns:
                return input_str
            else:
                interactive_print(f"Column '{input_str}' not found in the DataFrame")
                return None
    
    display_columns(df_columns, binarized_columns_history)
    display_menu()
    
    while True:
        user_input = scan_input("Enter command: ")
        
        if user_input == 'done':
            break
        elif user_input == 'l':
            display_columns(list(df_result.columns), binarized_columns_history)
            continue
        elif user_input == 'h':
            display_menu()
            continue
        elif user_input == 'k':
            # Toggle auto-removal of base columns
            auto_remove_base_columns = not auto_remove_base_columns
            status = "ENABLED" if auto_remove_base_columns else "DISABLED"
            interactive_print(f"Auto-removal of base columns is now {status}")
            continue
        elif user_input == 's':
            if binarized_columns_history:
                interactive_print("\n=== Binarized Columns Summary ===")
                for i, (src_col, new_col, threshold, threshold_type, _) in enumerate(binarized_columns_history):
                    src_display = src_col
                    if isinstance(src_col, list):
                        src_display = ", ".join(src_col)
                    
                    removed_status = " [REMOVED]" if new_col not in df_result.columns else ""
                    interactive_print(f"{i+1}. Source: {src_display} → New: {new_col}{removed_status}")
                    interactive_print(f"   Threshold: {threshold} (Type: {threshold_type})")
                    if new_col in df_result.columns:
                        interactive_print(f"   Distribution: {df_result[new_col].value_counts().to_dict()}")
            else:
                interactive_print("No columns have been binarized yet.")
            continue
        elif user_input == 'r':
            # Option to remove a binarized column
            if not binarized_columns_history:
                interactive_print("No binarized columns to remove.")
                continue
                
            interactive_print("\n=== Remove Binarized Column ===")
            for i, (src_col, new_col, _, _, _) in enumerate(binarized_columns_history):
                if new_col in df_result.columns:
                    src_display = src_col
                    if isinstance(src_col, list):
                        src_display = ", ".join(src_col)
                    interactive_print(f"[{i}] {new_col} (from {src_display})")
            
            try:
                remove_input = scan_input("Enter index or range of columns to remove ('2', '2-4', or -1 to cancel): ")
                if remove_input == '-1':
                    continue

                try:
                    if '-' in remove_input:
                        # Handle range input
                        start_idx, end_idx = map(int, remove_input.split('-'))
                        if 0 <= start_idx <= end_idx < len(binarized_columns_history):
                            for remove_idx in range(start_idx, end_idx + 1):
                                _, col_to_remove, _, _, _ = binarized_columns_history[remove_idx]
                                if col_to_remove in df_result.columns:
                                    df_result = df_result.drop(columns=[col_to_remove])
                                    interactive_print(f"Removed column: {col_to_remove}")
                                else:
                                    interactive_print(f"Column {col_to_remove} has already been removed.")
                        else:
                            interactive_print("Invalid range! Please enter valid indices.")
                    else:
                        # Handle single index input
                        remove_idx = int(remove_input)
                        if 0 <= remove_idx < len(binarized_columns_history):
                            _, col_to_remove, _, _, _ = binarized_columns_history[remove_idx]
                            if col_to_remove in df_result.columns:
                                df_result = df_result.drop(columns=[col_to_remove])
                                interactive_print(f"Removed column: {col_to_remove}")
                            else:
                                interactive_print(f"Column {col_to_remove} has already been removed.")
                        else:
                            interactive_print("Invalid index!")
                except ValueError:
                    interactive_print("Invalid input! Please enter a valid index or range.")
            except ValueError:
                interactive_print("Please enter a valid number")
            
            continue
        elif user_input == 'a':
            # Automatic replacement of values across all columns
            interactive_print("\n=== Automatic String Replacement ===")
            interactive_print("This will replace specific values with '1' or ''0'' across selected columns.")
            
            # Get columns to process
            current_columns = list(df_result.columns)
            display_columns(current_columns, binarized_columns_history)
            
            col_input = scan_input("\nEnter column indices or names separated by commas (leave empty for all columns):")
            
            if col_input:
                # Parse each item (could be index or name)
                items = [item.strip() for item in col_input.split(',')]
                columns_to_process = []
                
                for item in items:
                    col = get_column_from_input(item, current_columns)
                    if col is not None:
                        columns_to_process.append(col)
                
                if not columns_to_process:
                    interactive_print("No valid columns selected!")
                    continue
            else:
                # Use all columns if no specific selection
                columns_to_process = current_columns
            
            # Get values to replace with "1"
            yes_list_input = scan_input("\nEnter values to replace with '1' (comma-separated):")
            yes_list = [item.strip() for item in yes_list_input.split(',') if item.strip()]
            
            
            if not yes_list:
                interactive_print("No replacement values provided, operation cancelled.")
                continue
            
            
            # Confirm the operation
            interactive_print("\nReady to perform the following replacements:")
            interactive_print(f"In columns: {', '.join(columns_to_process)}")
            interactive_print(f"Replace {yes_list} with '1'")
            
            # if is_interactive:
            #     confirm = input("\nConfirm operation? (y/n): ").strip().lower()
            #     if confirm != 'y':
            #         interactive_print("Operation cancelled.")
            #         continue
            
            # Perform replacements
            try:
                df_before = df_result.copy()
                
                # Track changes for reporting
                changes_made = 0
                affected_columns = []
                
                for col in columns_to_process:
                    binarizeColumn(df_result, col, col, yes_list, 'string_equals')
                
                # Report results
                if changes_made > 0:
                    interactive_print(f"\nReplacement complete! {changes_made} values replaced across {len(affected_columns)} columns.")
                    interactive_print(f"Affected columns: {', '.join(affected_columns)}")
                    
                    # Add affected columns to the tracking set
                    for col in affected_columns:
                        auto_replaced_columns.add(col)
                    
                    # Add to history with a special entry
                    binarized_columns_history.append(
                        (affected_columns, "MULTIPLE_COLUMNS", [yes_list], "auto_replacement", 
                         {"columns": len(affected_columns), "values_replaced": changes_made})
                    )
                else:
                    interactive_print("No values were replaced. Check your input values and try again.")
                    
            except Exception as e:
                print(f"Error during automatic replacement: {str(e)}")
                df_result = df_before  # Restore previous state on error
            
            continue
        else:
            # Check if it's a direct column selection (single index, name, or comma-separated list)
            current_columns = list(df_result.columns)
            source_columns = []
            
            # Try to parse as a comma-separated list first
            if ',' in user_input:
                # Multiple columns specified
                items = [item.strip() for item in user_input.split(',')]
                
                for item in items:
                    col = get_column_from_input(item, current_columns)
                    if col is not None:
                        source_columns.append(col)
                
                if not source_columns:
                    interactive_print("No valid columns selected! Type 'h' for help.")
                    continue
            else:
                # Try as single column
                col = get_column_from_input(user_input, current_columns)
                if col is not None:
                    source_columns = [col]
                else:
                    interactive_print(f"Unknown command or invalid column: '{user_input}'. Type 'h' for help.")
                    continue
            
            # If we got here, we have valid columns to binarize
            # Get new column name
            interactive_print(f"Selected column(s) for binarization: {', '.join(source_columns)}")
            new_column_name = scan_input("Enter name for the new binarized column: ")
            if not new_column_name:
                interactive_print("Column name cannot be empty!")
                continue
            
            is_overwriting = True
            if is_interactive:
                # Check if we're replacing an existing column
                is_overwriting = False
                if new_column_name in df_result.columns:
                    overwrite = input(f"Column '{new_column_name}' already exists. Overwrite? (y/n): ").lower()
                    if overwrite != 'y':
                        continue
                    is_overwriting = True
            
            # Check if we're replacing an original column
            replacing_originals = [col for col in source_columns if col == new_column_name]
            for col in replacing_originals:
                if col not in replaced_columns:
                    replaced_columns.append(col)
            
            # Ask if original columns should be dropped after binarization
            # Skip this question if the new column has the same name as a source column
            skip_drop_question = is_overwriting and any(col == new_column_name for col in source_columns)
            drop_originals = False
            
            if not skip_drop_question and not auto_remove_base_columns:
                drop_originals = scan_input("Drop original columns after binarization? (y/n): ")
                drop_originals = drop_originals == 'y'
            elif auto_remove_base_columns:
                drop_originals = True
                interactive_print("Original columns will be automatically removed (auto-removal enabled).")
            else:
                interactive_print("Note: Source column will be replaced with binarized version")
            
            # Get threshold type
            display_threshold_types()
            threshold_type = scan_input("Enter threshold type: ")
            
            valid_types = ['superior', 'inferior', 'superior_inferior', 
                           'equals', 'not_equals', 'string_equals', 'string_not_equals']
            if threshold_type not in valid_types:
                interactive_print(f"Invalid threshold type. Please choose from: {', '.join(valid_types)}")
                continue
            
            # Get threshold value
            if threshold_type == 'superior_inferior':
                try:
                    upper = float(scan_input("Enter upper threshold: "))
                    lower = float(scan_input("Enter lower threshold: "))
                    threshold = [upper, lower]
                except ValueError:
                    interactive_print("Please enter valid numbers for thresholds")
                    continue
            elif threshold_type in ['string_equals', 'string_not_equals']:
                threshold = scan_input("Enter string to search for: ")
            else:
                threshold_input = scan_input("Enter threshold value: ")
                try:
                    # Try to convert to numeric if possible
                    threshold = float(threshold_input)
                    # Convert to int if it's a whole number
                    if threshold.is_integer():
                        threshold = int(threshold)
                except ValueError:
                    threshold = threshold_input
            
            # Perform binarization
            try:
                interactive_print(f"\nBinarizing {', '.join(source_columns)} → {new_column_name}")
                interactive_print(f"Using threshold: {threshold} (Type: {threshold_type})")
                
                df_before = df_result.copy()
                df_result = binarizeColumn(
                    df_result, source_columns, new_column_name, threshold, threshold_type
                )
                
                # Store in history
                binarized_columns_history.append(
                    (source_columns, new_column_name, threshold, threshold_type, df_result[new_column_name].value_counts())
                )
                
                # Mark columns for removal if requested
                if drop_originals:
                    for col in source_columns:
                        # Don't mark the column for removal if it's the same as the new column name
                        if col != new_column_name and col not in columns_to_drop:
                            columns_to_drop.append(col)
                
                interactive_print(f"Binarization complete! Column '{new_column_name}' added.")
                if drop_originals:
                    cols_to_be_removed = [col for col in source_columns if col != new_column_name]
                    if cols_to_be_removed:
                        interactive_print(f"Original column(s) marked for removal at the end: {', '.join(cols_to_be_removed)}")
            except Exception as e:
                # Error message always displayed
                print(f"Error during binarization: {str(e)}")
                traceback.print_exc()
                df_result = df_before  # Restore previous state on error
    
    # Process removals: remove all base columns used in binarization operations
    # except those that were replaced with a column of the same name or modified by 'a' command
    if auto_remove_base_columns:
        base_columns_to_remove = set()
        for src_col, new_col, _, threshold_type, _ in binarized_columns_history:
            # Skip entries from auto replacement ('a' command)
            if threshold_type == "auto_replacement":
                continue
                
            if isinstance(src_col, list):
                for col in src_col:
                    # Only add column if it wasn't replaced and wasn't auto-replaced
                    if col != new_col and col not in replaced_columns and col not in auto_replaced_columns:
                        base_columns_to_remove.add(col)
            else:
                # Single column case
                if src_col != new_col and src_col not in replaced_columns and src_col not in auto_replaced_columns:
                    base_columns_to_remove.add(src_col)
        
        # Add to the columns_to_drop list
        for col in base_columns_to_remove:
            if col not in columns_to_drop:
                columns_to_drop.append(col)
                
        if base_columns_to_remove:
            interactive_print(f"\nAuto-removal marked {len(base_columns_to_remove)} base columns for removal")
    
    # Remove base columns if they were marked for removal
    if columns_to_drop:
        interactive_print("\n=== Removing Original Columns ===")
        removed_count = 0
        for col in columns_to_drop:
            if col in df_result.columns:
                df_result = df_result.drop(columns=[col])
                interactive_print(f"Removed original column: {col}")
                removed_count += 1
        
        interactive_print(f"Removed {removed_count} original columns in total.")
    
    # Summary - always displayed
    print(f"\n=== Summary: {len(binarized_columns_history)} columns binarized ===")
    if binarized_columns_history:
        for i, (src_col, new_col, threshold, threshold_type, _) in enumerate(binarized_columns_history):
            if isinstance(src_col, list):
                src_display = ", ".join(src_col) if len(src_col) < 3 else f"{len(src_col)} columns"
            else:
                src_display = src_col
                
            col_status = ""
            if new_col not in df_result.columns:
                col_status = " [REMOVED]"
                
            print(f"{i+1}. {src_display} → {new_col}{col_status} (Type: {threshold_type}, Threshold: {threshold})")
    
    # Display final column removal summary
    if columns_to_drop:
        removed_cols = [col for col in columns_to_drop if col not in df_result.columns]
        if removed_cols:
            print(f"\nRemoved {len(removed_cols)} original columns:")
            for col in removed_cols:
                print(f"- {col}")
    print("================================================\n")
    
    return df_result

def csv_to_slf(csv_path, slf_path):
    with open(csv_path, newline='') as f:
        reader = csv.reader(f)
        headers = next(reader)
        # assume first header is blank or 'Object'
        object_names = []
        matrix = []
        for row in reader:
            if not row: continue
            object_names.append(str(len(object_names)))
            # interpret presence: any non-zero/non-empty → '1', else '0'
            line = []
            for val in row:
                v = val.strip()
                line.append('1' if v and v not in ('0','false','False') else '0')
            matrix.append(line)

    attribute_names = headers
    n_objs = len(object_names)
    n_attrs = len(attribute_names)

    with open(slf_path, 'w', newline='') as f:
        f.write('[Lattice]\n')
        f.write(f'{n_objs}\n{n_attrs}\n')
        f.write('[Objects]\n')
        f.writelines(obj + '\n' for obj in object_names)
        f.write('[Attributes]\n')
        f.writelines(attr + '\n' for attr in attribute_names)
        f.write('[relation]\n')
        for row in matrix:
            f.write(' '.join(row) + ' ' + '\n')

if __name__ == "__main__":
    import os
    import sys
    
    parser = argparse.ArgumentParser(description='Process a CSV file and save the transformed data.')
    parser.add_argument('input_file', type=str, help='Path to the input CSV file')
    parser.add_argument('--output_file', type=str, default='output', help='Path to the input CSV file')
    parser.add_argument('--format', type=str, choices=['csv', 'slf'], default='csv',
                        help='Output format in non-interactive mode (csv or slf)')
    parser.add_argument('--non-interactive', action='store_true', 
                        help='Run in non-interactive mode with default settings')
    
    
    args = parser.parse_args()
    
    
    # Check if input is from terminal or redirected
    is_interactive = os.isatty(sys.stdin.fileno()) and not args.non_interactive
    
    # is_interactive = True  # Force interactive mode for testing
    # Function to print only in interactive mode
    def interactive_print(*print_args, **print_kwargs):
        if is_interactive:
            print(*print_args, **print_kwargs)
    
    try:
        # Load the spreadsheet
        df_raw = pd.read_csv(args.input_file, sep=';', encoding='latin-1')
    
        
        interactive_print(f"Spreadsheet loaded: {args.input_file}\n")
        
        df_modif = df_raw.copy()
        for col in df_modif.columns:
            # Remove leading and trailing spaces from column names
            df_modif.rename(columns={col: normalize_string(col)}, inplace=True)

        # Display initial information in interactive mode only
        interactive_print(f"Initial shape: {df_modif.shape}")
        interactive_print(f"Number of columns: {len(df_modif.columns)}")
        
        # Create main menu (only displayed in interactive mode)
        def display_main_menu():
            interactive_print("\n===== Main Menu =====")
            interactive_print("- Enter 'drop' to select columns to drop")
            interactive_print("- Enter 'bin' to binarize columns")
            interactive_print("- Enter 'info' to display current dataframe info")
            interactive_print("- Enter 'h' to show this menu again")
            interactive_print("- Enter 'export' to save the processed file")
            interactive_print("- Enter 'exit' to exit the program without saving")
        
        # Interactive mode
        display_main_menu()

        while True:
            user_choice = scan_input("\nEnter command: ")
            
            if user_choice == 'drop':
                # Column dropping functionality
                columns_to_drop = readColumnsToDrop(df_modif)
                if columns_to_drop:
                    df_modif = df_modif.drop(columns_to_drop, axis=1)
                    interactive_print(f"Dropped {len(columns_to_drop)} columns. Current shape: {df_modif.shape}")
                else:
                    interactive_print("No columns were selected for dropping.")
                    
            elif user_choice == 'bin':
                # Column binarization functionality
                df_modif = binarizeColumnsMenu(df_modif)
                interactive_print(f"Binarization complete. Current shape: {df_modif.shape}")
                
            elif user_choice == 'export':
                # Export the processed file
                csv_path = args.output_file.rsplit('.', 1)[0] + '.csv'
                df_modif.to_csv(csv_path, index=False, sep=';', encoding='latin-1')
                interactive_print(f"File exported as CSV to: {args.output_file + '.csv'}")
            
                # Generate an SLF file with the same base name
                slf_path = args.output_file.rsplit('.', 1)[0] + '.slf'
                
                df_modif.to_csv(csv_path, index=False)
                csv_to_slf(csv_path, slf_path)
                
                interactive_print(f"File exported as SLF to: {slf_path}")
                
                
                continue_edit = scan_input("Would you like to continue editing? (y/n): ")
                if continue_edit != 'y':
                    interactive_print("Processing complete!")
                    break
                    
            elif user_choice == 'info':
                # Display current dataframe information
                interactive_print(f"\n===== DataFrame Information =====")
                interactive_print(f"Current shape: {df_modif.shape}")
                interactive_print(f"Number of columns: {len(df_modif.columns)}")
                interactive_print(f"Number of rows: {len(df_modif)}")
                interactive_print(f"Column types:")
                for col, dtype in df_modif.dtypes.items():
                    interactive_print(f"  - {col}: {dtype}")
                    
            elif user_choice == 'exit':
                interactive_print("Exiting without saving.")
                break
            elif user_choice == 'h':
                display_main_menu()
                
            else:
                interactive_print("Invalid command.")
                display_main_menu()
                
    except FileNotFoundError:
        print(f"\nError: The file '{args.input_file}' was not found.")
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")
        traceback.print_exc()
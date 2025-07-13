import csv
import pandas as pd
import numpy as np
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
import argparse
import re
import os
import traceback

# Import all utility functions from the created py_utilis library
from py_utils import *

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
        if not is_interactive:
            return
    
        """Helper function to display columns with their indices"""
        interactive_print("\n=== Available Columns ===")
        for i, col in enumerate(cols_list):
            status = ""
            if col in to_drop:
                status = " [MARKED FOR REMOVAL]"
            interactive_print(f"[{i}] {col}{status}")
    
    display_columns(df_columns, columns_to_drop)
    display_column_removal_menu()
    
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
            display_column_removal_menu()
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
        if not is_interactive:
            return
        print("\n=== Available Columns ===")
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
                
            print(f"[{i}] {col}{status}")
    
    def display_threshold_types():
        """Helper function to display available threshold types"""
        interactive_print("\n=== Available Threshold Types ===")
        interactive_print("- 'superior': Mark when value < threshold")
        interactive_print("- 'inferior': Mark when value > threshold")
        interactive_print("- 'superior_inferior': Mark when threshold[1] < value < threshold[0]")
        interactive_print("- 'equals': Mark when value == threshold")
        interactive_print("- 'not_equals': Mark when value == threshold")
        interactive_print("- 'string_contains': Mark when string contains threshold")
        interactive_print("- 'string_not_contains': Mark when string doesn't contain threshold")
        interactive_print("- 'string_equals': Mark when string == threshold (for multiple values, if all are equal)")
        interactive_print("- 'string_not_equals': Mark when string != threshold (for multiple values, if all are different)")
    
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
            print(f"Auto-removal of base columns is now {status}")
            continue
        elif user_input == 's':
            if binarized_columns_history:
                print("\n=== Binarized Columns Summary ===")
                for i, (src_col, new_col, threshold, threshold_type, _) in enumerate(binarized_columns_history):
                    src_display = src_col
                    if isinstance(src_col, list):
                        src_display = ", ".join(src_col)
                    
                    removed_status = " [REMOVED]" if new_col not in df_result.columns else ""
                    print(f"{i+1}. {src_display} -> {new_col}{removed_status} (Type: {threshold_type}, Threshold: {threshold})")
                    if new_col in df_result.columns:
                        print(f"   Distribution: {df_result[new_col].value_counts().to_dict()}")
            else:
                print("No columns have been binarized yet.")
            continue
        elif user_input == 'r':
            # Option to remove a binarized column
            if not binarized_columns_history:
                print("No binarized columns to remove.")
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
            
           
            
            # Get values to replace with "1"
            yes_list_input = scan_input("\nEnter values to replace with '1' (comma-separated):")
            yes_list = [item.strip() for item in yes_list_input.split(',') if item.strip()]

            # Get values to replace with "1"
            yes_list_input = scan_input("\nEnter values to replace with '0' (comma-separated):")
            no_list = [item.strip() for item in yes_list_input.split(',') if item.strip()]
            
            
            if not yes_list and not no_list:
                interactive_print("No replacement values provided, operation cancelled.")
                continue
            
            # Confirm the operation
            interactive_print("\nReady to perform the following replacements:")
            # interactive_print(f"In columns: {', '.join(columns_to_process)}")
            interactive_print(f"Replace {yes_list} with '1'")
            interactive_print(f"Replace {no_list} with '0'")
            
            # if is_interactive:
            #     confirm = input("\nConfirm operation? (y/n): ").strip().lower()
            #     if confirm != 'y':
            #         interactive_print("Operation cancelled.")
            #         continue
            
            # Perform replacements
            try:
                df_before = df_result.copy()
                
                for val in yes_list:
                    # Normalize the value of the column and replace it with "1" if it matches the value
                    df_result = df_result.apply(lambda col: col.map(lambda x: "1" if normalize_string(x) == normalize_string(val) else x))
                for val in no_list:
                    # Normalize the value of the column and replace it with "0" if it matches the value
                    df_result = df_result.apply(lambda col: col.map(lambda x: "0" if normalize_string(x) == normalize_string(val) else x))
                
                print(f"\nReplacement complete! values replaced across all columns.")
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
            # if is_interactive:
            #     # Check if we're replacing an existing column
            #     is_overwriting = False
            #     if new_column_name in df_result.columns:
            #         overwrite = input(f"Column '{new_column_name}' already exists. Overwrite? (y/n): ").lower()
            #         if overwrite != 'y':
            #             continue
            #         is_overwriting = True
            
            # Check if we're replacing an original column
            replacing_originals = [col for col in source_columns if col == new_column_name]
            for col in replacing_originals:
                if col not in replaced_columns:
                    replaced_columns.append(col)
            
            # Ask if original columns should be dropped after binarization
            # Skip this question if the new column has the same name as a source column
            # skip_drop_question = is_overwriting and any(col == new_column_name for col in source_columns)
            drop_originals = True
            
            # if not skip_drop_question and not auto_remove_base_columns:
            #     drop_originals = scan_input("Drop original columns after binarization? (y/n): ")
            #     drop_originals = drop_originals == 'y'
            # elif auto_remove_base_columns:
            #     drop_originals = True
            #     interactive_print("Original columns will be automatically removed (auto-removal enabled).")
            # else:
            #     interactive_print("Note: Source column will be replaced with binarized version")
            
            # Get threshold type
            display_threshold_types()
            threshold_type = scan_input("Enter threshold type: ")
            
            valid_types = ['superior', 'inferior', 'superior_inferior', 
                           'equals', 'not_equals', 'string_contains', 'string_not_contains', 'string_equals', 'string_not_equals']
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
            elif threshold_type in ['string_contains', 'string_not_contains']:
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
                df_result = binarize_column(
                    df_result, source_columns, new_column_name, threshold, threshold_type
                )
                
                # Store in history
                binarized_columns_history.append(
                    (source_columns, new_column_name, threshold, threshold_type, df_result[new_column_name].value_counts())
                )
                
                # Mark columns for removal if auto removal is enabled
                if auto_remove_base_columns:
                    for col in source_columns:
                        # Don't mark the column for removal if it's the same as the new column name
                        if col != new_column_name and col not in columns_to_drop:
                            columns_to_drop.append(col)
                
                interactive_print(f"Binarization complete! Column '{new_column_name}' added.")
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
                
            print(f"{i+1}. {src_display} -> {new_col}{col_status} (Type: {threshold_type}, Threshold: {threshold})")
    
    # Display final column removal summary
    if columns_to_drop:
        removed_cols = [col for col in columns_to_drop if col not in df_result.columns]
        if removed_cols:
            print(f"\nRemoved {len(removed_cols)} original columns:")
            for col in removed_cols:
                print(f"- {col}")
    print("================================================\n")
    
    return df_result

def removeRowsByValue(df):
    """
    Interactive function to remove rows based on specific value(s) in a selected column.
    Args:
        df (pandas.DataFrame): The DataFrame to modify.
    Returns:
        pandas.DataFrame: The modified DataFrame with rows removed.
    """
    interactive_print("\n===== Remove Rows by Value =====")

    # Display available columns
    interactive_print("\nAvailable columns:")
    for i, col in enumerate(df.columns):
        interactive_print(f"[{i}] {col}")

    # Get the column name from the user
    column_name = scan_input("Enter the column name or index to filter rows: ")
    try:
        # Allow selection by index or name
        if column_name.isdigit():
            column_index = int(column_name)
            if 0 <= column_index < len(df.columns):
                column_name = df.columns[column_index]
            else:
                interactive_print("Invalid column index.")
                return df
        elif column_name not in df.columns:
            interactive_print(f"Column '{column_name}' does not exist in the DataFrame.")
            return df
    except ValueError:
        interactive_print("Invalid input. Please enter a valid column name or index.")
        return df

    interactive_print("\nColumn ${column_name} unique values:\n")
    if(is_interactive):
        list_column_unique_values(df, column_name)
    interactive_print("\n")



    # Choose removal type
    interactive_print("\nRemoval types available:")
    interactive_print("1. equals (remove rows where value matches)")
    interactive_print("2. not_equals (remove rows where value does NOT match)")
    interactive_print("3. between_interval (remove rows where value is BETWEEN two numbers)")
    interactive_print("4. outside_interval (remove rows where value is OUTSIDE two numbers)")
    removal_type_input = scan_input("Choose removal type (1/2/3/4): ").strip()
    removal_types = {
        "1": "equals",
        "2": "not_equals",
        "3": "between_interval",
        "4": "outside_interval"
    }
    threshold_type = removal_types.get(removal_type_input)
    if not threshold_type:
        interactive_print("Invalid removal type selected.")
        return df

    # Get the value(s) to filter rows
    if threshold_type in ["equals", "not_equals"]:
        value_to_remove = scan_input(
            f"Enter the value(s) to remove rows where '{column_name}' {'matches' if threshold_type == 'equals' else 'does NOT match'} (comma-separated for multiple values): "
        )
        values_list = [normalize_string(v.strip()) for v in value_to_remove.split(",") if v.strip()]
        threshold = values_list if len(values_list) > 1 else values_list[0]
    elif threshold_type in ["between_interval", "outside_interval"]:
        min_val = scan_input("Enter minimum value of interval: ")
        max_val = scan_input("Enter maximum value of interval: ")
        try:
            min_val = float(min_val)
            max_val = float(max_val)
            threshold = [min_val, max_val]
        except ValueError:
            interactive_print("Invalid interval values. Please enter numeric values.")
            return df

    rows_before = len(df)
    df = remove_rows_by_match(df, column_name, threshold, threshold_type, is_interactive=True)
    rows_after = len(df)

    print(f"Removed {rows_before - rows_after} rows using '{threshold_type}' on '{column_name}' with threshold {threshold}.")
    return df

if __name__ == "__main__":
    import os
    import sys
    
    parser = argparse.ArgumentParser(description='Process a CSV file and save the transformed data.')
    parser.add_argument('input_file', type=str, help='Path to the input CSV file')
    parser.add_argument('output_file', type=str, help='Path to the input CSV file')
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
                
            elif user_choice == 'remove':
                # Row removal functionality
                df_modif = removeRowsByValue(df_modif)
                
            elif user_choice == 'export':
                # Export the processed file
                prefix = args.output_file.rsplit('.', 1)[0] if '.' in args.output_file else args.output_file
                csv_path = prefix + '.csv'
                df_modif.to_csv(csv_path, index=False, sep=';', encoding='latin-1')
                slf_path = prefix + '.slf'
                SlfConversion.csv_to_slf(csv_path, slf_path)
                interactive_print(f"File exported as CSV to: {csv_path}")
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
"""
Column binarization utilities for DataFrame processing
"""
import numpy as np
import pandas as pd
from .string_utils import (
    normalize_string, arrayTest, arrayStringContainsTest, 
    arrayStringEqualsTest, arrayStringTestNot
)
from .ui_utils import interactive_print


def binarize_column(df, column_names, new_column_name, threshold, threshold_type, is_interactive=True):
    """
    Binarizes one or multiple columns in the DataFrame based on a threshold.
    
    Args:
        df: DataFrame to be modified
        column_names: Name(s) of column(s) to be binarized (string or list of strings)
        new_column_name: Name of the column after binarization
        threshold: Threshold for binarization
        threshold_type: Type of threshold ('superior', 'inferior', 'superior inferior', 
                      'equals', 'not equals', 'string contains', 'string not contains',
                        'string equals' or 'string not equals')
        is_interactive: Whether to print interactive messages
        
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
    
    interactive_print(f"Performing binarization on columns: {', '.join(valid_columns)}", is_interactive=is_interactive)

    # Create a temporary working column if multiple columns are provided
    if threshold_type in ['string_contains', 'string_not_contains', 'string_equals', 'string_not_equals']:
        # Create concatenated string column for text search
        df['_temp_combined'] = df[valid_columns].astype(str).apply(lambda col: col.map(normalize_string)).agg(lambda x: '.' + '.'.join(x) + '.', axis=1)
        # Replace NaN values with 'n/a' in the temporary column
        df['_temp_combined'] = df['_temp_combined'].fillna('n/a')
        working_column = '_temp_combined'
        print(f"Temporary column created for string search: {df['_temp_combined'].value_counts()}")
        print(f"{df['_temp_combined'].head()}")
    elif len(valid_columns) > 1:
        # Choose appropriate combination based on threshold_type
        if threshold_type in ('superior', 'not_Equals'):
            # Use any (logical OR) - if any column meets condition
            df['_temp_combined'] = df[valid_columns].min(axis=1)
        elif threshold_type in ('inferior', 'equals'):
            # Use all (logical AND) - all columns must meet condition
            df['_temp_combined'] = df[valid_columns].max(axis=1)
        elif threshold_type == 'superior_inferior':
            # For range checks, use the mean of each row
            df['_temp_combined'] = df[valid_columns].mean(axis=1)
        working_column = '_temp_combined'
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
    elif threshold_type == 'string_contains':
        if "," not in threshold:
            df[new_column_name] = np.where(arrayStringContainsTest([threshold], df[working_column].str), "1", "0")
        else:
            threshold = threshold.split(",")
            df[new_column_name] = np.where(arrayStringContainsTest(threshold, df[working_column].str), "1", "0")
    elif threshold_type == 'string_not_contains':
        if "," not in threshold:
            df[new_column_name] = np.where(arrayStringContainsTest([threshold], df[working_column].str), "0", "1")
        else:
            threshold = threshold.split(",")
            df[new_column_name] = np.where(arrayStringContainsTest(threshold, df[working_column].str), "0", "1")
    elif threshold_type == 'string_equals':
        if "," not in threshold:
            df[new_column_name] = np.where(arrayStringEqualsTest([threshold], df[working_column].str, valid_columns), "1", "0")
        else:
            threshold = threshold.split(",")
            df[new_column_name] = np.where(arrayStringEqualsTest(threshold, df[working_column].str, valid_columns), "1", "0")
    elif threshold_type == 'string_not_equals':
        if "," not in threshold:
            df[new_column_name] = np.where(arrayStringEqualsTest([threshold], df[working_column].str, valid_columns), "0", "1")
        else:
            threshold = threshold.split(",")
            df[new_column_name] = np.where(arrayStringEqualsTest(threshold, df[working_column].str, valid_columns), "0", "1")
    else:
        print(f"Invalid threshold type: {threshold_type}. Use 'superior', 'inferior', etc.")
        return df
    
    # Clean up temporary column if it was created
    if len(valid_columns) > 1 and '_temp_combined' in df.columns:
        df = df.drop('_temp_combined', axis=1)
    
    print(f"{df[new_column_name].value_counts()}\n")
    
    return df

def remove_rows_by_match(df, column_names, threshold, threshold_type, is_interactive=True):
    """
    Remove rows from DataFrame based on match criteria.
    Args:
        df: DataFrame to modify
        column_names: Name(s) of column(s) to check (string or list)
        threshold: Value(s) for comparison (single value or list)
        threshold_type: 'between_interval', 'outside_interval', 'equals', 'not_equals'
        is_interactive: Print messages if True
    Returns:
        pandas.DataFrame: Modified DataFrame
    """
    # Convert to list for consistency
    if isinstance(column_names, str):
        column_names = [column_names]
    valid_columns = [col for col in column_names if col in df.columns]
    if not valid_columns:
        print(f"Warning: None of the specified columns {column_names} exist in the DataFrame")
        return df

    working_column = valid_columns[0] if len(valid_columns) == 1 else valid_columns

    # Normalize column values for comparison
    col_series = df[working_column].astype(str).map(normalize_string)

    if threshold_type == "between_interval":
        mask = (df[working_column] >= threshold[0]) & (df[working_column] <= threshold[1])
        df = df[~mask]
    elif threshold_type == "outside_interval":
        mask = (df[working_column] < threshold[0]) | (df[working_column] > threshold[1])
        df = df[~mask]
    elif threshold_type == "equals":
        # Support list of values
        if isinstance(threshold, (list, tuple, set)):
            normalized_values = [normalize_string(str(v)) for v in threshold]
            mask = col_series.isin(normalized_values)
        else:
            try:
                    threshold = normalize_string(str(threshold))
            except ValueError:
                threshold = normalize_string(str(threshold))
            mask = col_series == threshold
        df = df[~mask]
    elif threshold_type == "not_equals":
        # Support list of values
        if isinstance(threshold, (list, tuple, set)):
            normalized_values = [normalize_string(str(v)) for v in threshold]
            mask = col_series.isin(normalized_values)
        else:
            try:
                    threshold = normalize_string(str(threshold))
            except ValueError:
                threshold = normalize_string(str(threshold))
            mask = col_series == threshold
        df = df[mask]
    else:
        print(f"Invalid threshold type: {threshold_type}.")
        return df

    if is_interactive:
        print(f"Rows removed for {threshold_type} with threshold {threshold} on columns {working_column}.")
    return df

def clone_column(df, original_column, new_column):
    """
    Clones a column in the DataFrame to a new column name.
    Args:
        df (pandas.DataFrame): The DataFrame to modify.
        original_column (str): The name of the column to clone.
        new_column (str): The name of the new column.
    Returns:
        pandas.DataFrame: Modified DataFrame with the cloned column.
    """
    if original_column not in df.columns:
        print(f"Column '{original_column}' does not exist in the DataFrame.")
        return df
    df[new_column] = df[original_column].copy()
    interactive_print(f"Column '{original_column}' cloned to '{new_column}'.")
    return df
    

def list_column_unique_values(df, column):
    """
    Lists unique values in a DataFrame column.
    Args:
        df (pandas.DataFrame): The DataFrame to inspect.
        column (str): The column name.
    Returns:
        list: Unique values in the column.
    """
    if column not in df.columns:
        print(f"Column '{column}' does not exist in the DataFrame.")
        return []
    unique_values = df[column].unique()
    print(f"Unique values in column '{column}':")
    for val in unique_values:
        print(f"- {val}")
    return unique_values.tolist()
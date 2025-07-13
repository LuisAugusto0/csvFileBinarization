"""
String utility functions for data processing and normalization
"""
import re
import pandas as pd


def normalize_string(name):
    """Normalize a column name by removing whitespace and replacing special characters (excluding hyphen and comma) with underscores"""
    name = str(name).strip().lower()  # Convert to string, strip whitespace, and lowercase
    name = re.sub(r'[^\w\s/,-]', '_', name)  # Replace non-word/non-space/non-hyphen/non-comma chars with _
    name = re.sub(r'\s+', '_', name)      # Replace spaces with _
    name = re.sub(r'_+', '_', name)        # Collapse multiple _ into one
    name = name.strip('_')  # Remove any _ at the start or end of the string
    return name


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


def arrayStringContainsTest(array, string_methods):
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
        threshold = f".{threshold}."
        result = result | string_methods.contains(threshold, na=False)
    
    return result


def arrayStringEqualsTest(array, string_methods, valid_columns):
    """
    Tests if any of the values in the array is contained in the given string series
    
    Args:
        array: Array of strings to check for
        string_methods: The string accessor (Series.str) to check against
        valid_columns: List of valid column names
        
    Returns:
        Series: Boolean Series with True where any value in array is found
    """
    # For each threshold, update the mask where the strings contain that threshold
    print(f"Array: {array}")
    print(f"Valid columns: {valid_columns}")
    number_of_columns = len(valid_columns)
    print(f"Number of columns: {number_of_columns}")
    i = 0
    for threshold in array:
        thresholdFinal = ""
        for _ in range(number_of_columns):
            thresholdFinal += threshold + "."
        thresholdFinal = thresholdFinal[:-1]  # Remove the last dot
        array[i] = thresholdFinal
        print(f"threshold final{i}: {array[i]}")
        i += 1
    
    return arrayStringContainsTest(array, string_methods)


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
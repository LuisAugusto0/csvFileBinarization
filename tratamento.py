import csv
import pandas as pd
import numpy as np
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
import argparse

def arrayTest (array, value):
    """
    Testa se o valor está no array
    @param array: Array a ser testado
    @param value: Valor (numero) a ser testado
    @return: True se o valor estiver no array, False caso contrário
    """
    for i in range(len(array)):
        if array[i] == value:
            return True
    return False

def arrayStringTest (array, value):
    """
    Testa se o valor está no array
    @param array: Array a ser testado
    @param value: Valor (String) a ser testado
    @return: True se o valor estiver no array, False caso contrário
    """
    for i in range(len(array)):
        if array[i].contains(value, na=False):
            return True
    return False

    
def binarizeNumericColumn(df, column_names, new_column_name, threshold, threshold_type):
    """
    Binarizes one or multiple columns in the DataFrame based on a threshold.
    
    @param df: DataFrame to be modified
    @param column_names: Name(s) of column(s) to be binarized (string or list of strings)
    @param new_column_name: Name of the column after binarization
    @param threshold: Threshold for binarization
    @param threshold_type: Type of threshold ('superior', 'inferior', 'superior_inferior', 
                          'equals', 'not_Equals', 'string_Equals' or 'string_Not_Equals')
    @return: Modified DataFrame
    """
    # Convert single column name to list for consistent handling
    if isinstance(column_names, str):
        column_names = [column_names]
    
    # Verify that at least one column exists in the DataFrame
    valid_columns = [col for col in column_names if col in df.columns]

    # Print warning for the columns that do not exist
    if len(valid_columns) != len(column_names):
        missing_columns = set(column_names) - set(valid_columns)
        print("=== Warning ===")
        print(f"The following columns do not exist in the DataFrame:\n{'\n'.join(missing_columns)}")
        print("Proceeding with the existing columns.")
        print("=== End of Warning ===\n")
    
    if not valid_columns:
        print(f"Warning: None of the specified columns {column_names} exist in the DataFrame")
        return df
    
    print(f"Realizando binarização das colunas: {', '.join(valid_columns)}")
    
    # Create a temporary working column if multiple columns are provided
    if len(valid_columns) > 1:
        # Choose appropriate combination based on threshold_type
        if threshold_type in ('superior', 'not_Equals'):
            # Use any (logical OR) - if any column meets condition
            df['_temp_combined'] = df[valid_columns].min(axis=1)
        elif threshold_type in ('inferior', 'equals'):
            # Use all (logical AND) - all columns must meet condition
            df['_temp_combined'] = df[valid_columns].max(axis=1)
        elif threshold_type == 'string_Equals':
            # Create concatenated string column for text search
            df['_temp_combined'] = df[valid_columns].astype(str).agg(' '.join, axis=1)
        elif threshold_type == 'string_Not_Equals':
            # Create concatenated string column for text search
            df['_temp_combined'] = df[valid_columns].astype(str).agg(' '.join, axis=1)
        elif threshold_type == 'superior_inferior':
            # For range checks, use the mean of each row
            df['_temp_combined'] = df[valid_columns].mean(axis=1)
        else:
            print(f"Warning: Threshold type '{threshold_type}' not supported for multiple columns")
            return df
        
        # Use the temporary column for the binarization
        working_column = '_temp_combined'
    else:
        # Use the single valid column directly
        working_column = valid_columns[0]
    
    # Perform the binarization based on threshold_type
    if threshold_type == 'superior':
        df[new_column_name] = np.where(df[working_column] < threshold, "X", "")
    elif threshold_type == 'inferior':
        df[new_column_name] = np.where(df[working_column] > threshold, "X", "")
    elif threshold_type == 'superior_inferior':
        df[new_column_name] = np.where((df[working_column] < threshold[0]) & (df[working_column] > threshold[1]), "X", "")
    elif threshold_type == 'equals':
        if isinstance(threshold, (int, float)):
            df[new_column_name] = np.where(df[working_column] == threshold, "X", "")
        else:
            df[new_column_name] = np.where(arrayTest(df[working_column], threshold), "X", "")
    elif threshold_type == 'not_Equals':
        if isinstance(threshold, (int, float)):
            df[new_column_name] = np.where(df[working_column] != threshold, "X", "")
        else:
            df[new_column_name] = np.where(not arrayTest(df[working_column], threshold), "X", "")
    elif threshold_type == 'string_Equals':
        if isinstance(threshold, str):
            df[new_column_name] = np.where(df[working_column].str.contains(threshold, na=False), "X", "")
        else:
            df[new_column_name] = np.where(arrayStringTest(df[working_column].str, threshold), "X", "")
    elif threshold_type == 'string_Not_Equals':
        if isinstance(threshold, str):
            df[new_column_name] = np.where(~df[working_column].str.contains(threshold, na=False), "", "X")
        else:
            df[new_column_name] = np.where(not arrayStringTest(df[working_column].str, threshold), "", "X")
    else:
        print("Tipo de threshold inválido. Use 'superior', 'inferior', etc.")
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
    print("\n===== Columns to drop menu =====")
    
    def display_columns(cols_list, to_drop):
        """Helper function to display columns with their indices"""
        print("\n=== Available Columns ===")
        for i, col in enumerate(cols_list):
            status = ""
            if col in to_drop:
                status = " [MARKED FOR REMOVAL]"
            print(f"[{i}] {col}{status}")
    
    def display_menu():
        """Helper function to display menu options"""
        print("\n=== Column Removal Options ===")
        print("- Enter a single index (e.g. '5') to mark a column for removal")
        print("- Enter a range (e.g. '5-10') to mark multiple columns for removal")
        print("- Enter 'u' to access the undo menu")
        print("- Enter 'l' to list all columns again")
        print("- Enter 'r' to display only columns marked for removal")
        print("- Enter 'h' to this menu again")
        print("- Enter 'done' to finish selection")
    
    display_columns(df_columns, columns_to_drop)
    display_menu()
    
    while True:
        user_input = input("\nEnter command: ").strip().lower()
        
        if user_input == 'done':
            break
        elif user_input == 'l':
            display_columns(df_columns, columns_to_drop)
            continue
        elif user_input == 'r':
            if columns_to_drop:
                print("\n=== Columns Marked for Removal ===")
                for i, col in enumerate(columns_to_drop):
                    reason = ""
                    for c, r in removed_columns_history:
                        if c == col:
                            reason = f" - Reason: {r}"
                            break
                    print(f"{i}. {col}{reason}")
            else:
                print("No columns are currently marked for removal.")
            continue
        elif user_input == 'u':
            if not removed_columns_history:
                print("No actions to undo!")
                continue
                
            print("\n=== Undo Menu ===")
            print("Recently removed columns:")
            for i, (col, reason) in enumerate(removed_columns_history):
                print(f"{i}. {col} - {reason}")
            
            undo_input = input("Enter index to restore (or 'back' to return): ")
            if undo_input.lower() == 'back':
                continue
                
            try:
                undo_index = int(undo_input)
                if 0 <= undo_index < len(removed_columns_history):
                    col_to_restore, _ = removed_columns_history.pop(undo_index)
                    if col_to_restore in columns_to_drop:
                        columns_to_drop.remove(col_to_restore)
                        print(f"Restored column: {col_to_restore}")
                    else:
                        print(f"Warning: Column {col_to_restore} was not in removal list")
                else:
                    print("Invalid index!")
            except ValueError:
                print("Please enter a valid number")
            continue
        elif user_input == 'h':
            display_menu()
            continue

        try:
            # Parse range input
            if '-' in user_input:
                start, end = map(int, user_input.split('-'))
                # Ensure valid range
                if 0 <= start <= end < len(df_columns):
                    # Add columns to drop list with reason
                    for i in range(start, end + 1):
                        col = df_columns[i]
                        if col not in columns_to_drop:
                            columns_to_drop.append(col)
                            removed_columns_history.append((col, f"Manual selection (range {start}-{end})"))
                    print(f"Marked columns {start} to {end} for removal")
                else:
                    print("Invalid range! Please enter valid column indices.")
            else:
                # Single column case
                index = int(user_input)
                if 0 <= index < len(df_columns):
                    col = df_columns[index]
                    if col not in columns_to_drop:
                        columns_to_drop.append(col)
                        removed_columns_history.append((col, f"Manual selection (index {index})"))
                        print(f"Marked column '{col}' for removal")
                    else:
                        print(f"Column '{col}' is already marked for removal")
                else:
                    print("Invalid index! Please enter a valid column index.")
        except ValueError:
            print("Invalid input! Please use the format shown in the menu.")
    
    # Summary
    print(f"\n=== Summary: {len(columns_to_drop)} columns selected for removal ===")
    if columns_to_drop:
        for col in columns_to_drop:
            print(f"- {col}")
    print("================================================\n")
    return columns_to_drop

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

def base_csv_pre_processing(csv_path, result_csv_path):
    # Carrega a planilha
    df_raw = pd.read_csv(csv_path, sep=';', encoding='latin-1')
    columns_to_drop = list()
    print(f"Planilha carregada: {csv_path}\n")

    # df_raw = df_raw.drop(list(df_raw.columns[0:6]) + 
    #                      list(df_raw.columns[7:20]) + 
    #                      list(df_raw.columns[21:24]) + 
    #                      list(df_raw.columns[25:26]) + 
    #                      list(df_raw.columns[28:29]) +
    #                      list(df_raw.columns[34:36]) +
    #                      list(df_raw.columns[43:45]) +
    #                      list(df_raw.columns[53:54]) +
    #                      list(df_raw.columns[55:56]) +
    #                      list(df_raw.columns[57:62]) +
    #                      list(df_raw.columns[68:79]) +
    #                      list(df_raw.columns[80:83]), axis=1)

    df_raw = df_raw.drop(readColumnsToDrop(df_raw), axis=1)

    df_modif = df_raw.copy()


    # Binarizar as colunas
    # Duration of pain before consultation (days)
    columns_to_drop.append("Duration of pain  before consultation (days)")
    df_modif = binarizeNumericColumn(df_modif, 
                                       "Duration of pain  before consultation (days)", "One week or more of pain before consultation", 
                                       6, "inferior")
    # Oxigen saturation (SaO2) at admission
    columns_to_drop.append("Oxygen saturation (SaO2) at admission")
    df_modif = binarizeNumericColumn(df_modif, 
                                       "Oxygen saturation (SaO2) at admission", "Low or very low oxigen saturation", 
                                       95, "superior")
    # Auxiliary temperature (°C)
    columns_to_drop.append("Axillary temperature (°C)")
    df_modif = binarizeNumericColumn(df_modif, 
                                       "Axillary temperature (°C)", "High auxiliar temperature (ºc)", 
                                       38, "inferior")
    # Respiratory rate
    columns_to_drop.append("Respiratory rate")
    df_modif = binarizeNumericColumn(df_modif, 
                                       "Respiratory rate", "High respiratory rate", 
                                       60, "inferior")
    # Heart rate
    columns_to_drop.append("Heart rate")
    df_modif = binarizeNumericColumn(df_modif, 
                                       "Heart rate", "Low heart rate", 
                                       100, "superior")
    # Rhinovirus in dna
    columns = ["Detection of DNA/RNA (TrueScience Respifinder Pathogen Identification Panel)                                                      Allele  1",
               "Detection of DNA/RNA (TrueScience Respifinder Pathogen Identification Panel)                                                        Allele  2",
               "Detection of DNA/RNA (TrueScience Respifinder Pathogen Identification Panel)                                              Allele  3",
               "Detection of DNA/RNA (TrueScience Respifinder Pathogen Identification Panel)                                               Allele  4",
               "Detection of DNA/RNA (TrueScience Respifinder Pathogen Identification Panel)                                             Allele  5",]
    df_modif = binarizeNumericColumn(df_modif,
                                       columns, "Rhinovirus in dna",
                                       "Rhinovirus", "string_Equals")
    print (df_modif["Rhinovirus in dna"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process a CSV file and save the transformed data.')
    parser.add_argument('input_file', type=str, help='Path to the input CSV file')
    parser.add_argument('output_file', type=str, help='Path where the output CSV file will be saved')
    
    args = parser.parse_args()
    
    
    try:
        # Carrega a planilha
        df_raw = pd.read_csv(args.input_file, sep=';', encoding='latin-1')
        print(f"\nProcessing complete! File saved to {args.output_file}")
    except FileNotFoundError:
        print(f"\nError: The file '{args.output_file}' was not found.")
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")
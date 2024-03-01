import pandas as pd


def read_and_export_csv_to_text(csv_file_path):
    # Read the CSV file into a DataFrame
    df_from_csv = pd.read_csv(csv_file_path)

    # Round the values in the DataFrame to the nearest integer
    df_rounded = df_from_csv.round()

    # Export the DataFrame to a string representation
    text_representation = df_rounded.to_string(index=False, col_space=8)

    # Print the text representation of the DataFrame
    print(text_representation)


# Replace the csv_file_path with your own CSV file path
csv_file_path = 'C://N-20W1PF3T3YXB-Data//h4zhang//Downloads//table.csv'
read_and_export_csv_to_text(csv_file_path)

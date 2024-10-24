import openpyxl

def merge_columns(input_file, output_file):
    wb = openpyxl.load_workbook(input_file)
    ws = wb.active

    for row in ws.iter_rows(min_row=1):
        merged_data = ""
        for cell in row[1:21]:  # B to U is columns 2 to 21
            merged_data += str(cell.value) + "\t"
        row[0].value = merged_data.rstrip("\t")

    wb.save(output_file)

if __name__ == "__main__":
    input_filename = "C:\\Users\\yixin\\Downloads\\test.xlsx"
    output_filename = "C:\\Users\\yixin\\Downloads\\output.xlsx"
    merge_columns(input_filename, output_filename)

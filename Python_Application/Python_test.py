import subprocess

text2pcap_path = r"C:\Application\Wireshark\text2pcap.exe"
original_string = "000E402000000000FACE401800C60014000003002800020001002900020001F124400100"
protocol = '62'


def preprocess_string(string, space_interval=2):
    new_string = '0000 ' + ' '.join(string[i:i+space_interval] for i in range(0, len(string), space_interval))
    return new_string


def save_to_txt(string, filename):
    with open(filename, 'w') as f:
        f.write(string)


def convert_to_pcap(input_filename, output_filename):
    command = f'"{text2pcap_path}" -S 1234,1234,{protocol} {input_filename} {output_filename}'
    subprocess.run(command, shell=True)


# 预处理字符串
preprocessed_string = preprocess_string(original_string)

# 保存为 txt 文件
txt_filename = "pkg.txt"
save_to_txt(preprocessed_string, txt_filename)

# 调用 text2pcap.exe
pcap_filename = "pkg.pcap"
convert_to_pcap(txt_filename, pcap_filename)

print("Conversion completed")

keys = ['key1', 'key2', 'key3']
values1 = ['value1_1', 'value1_2', 'value1_3']
values2 = ['value2_1', 'value2_2', 'value2_3']

my_dict = dict(zip(keys, zip(values1, values2)))
key = 'key2'

value1, value2 = my_dict[key]
print("Value 1:", value1)
print("Value 2:", value2)

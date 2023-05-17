A = [1, 2, 3, 2, 4, 5, 3, 6, 1, 7]  # 列表 A
B = []  # 列表 B

mapping_cache = {}  # 缓存映射结果的字典


def map_a_to_b(value):
    mapping = {1: 'A', 2: 'B', 3: 'C', 4: 'D', 5: 'E', 6: 'F', 7: 'G'}
    return mapping[value]
# 假设这里是映射函数的具体实现
# 根据 element 计算映射结果
# 返回映射结果


for element in A:
    if element not in mapping_cache:
        mapped_element = map_a_to_b(element)
        mapping_cache[element] = mapped_element
    else:
        mapped_element = mapping_cache[element]
    B.append(mapped_element)

print(B)

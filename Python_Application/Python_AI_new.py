# import re
#
# feature_id = "CB008311"
# feature_set = ['CB008311-A-123', 'CB008311-B-asdf', 'CB008311-B-', 'CB008311-C-A', 'CNI-72007-C_CB008311-A-1', 'CB008311-C']
#
# pattern = r'^{}-[^-]*'.format(re.escape(feature_id))
# filtered_set = []
#
# for s in feature_set:
#     match = re.match(pattern, s)
#     if match:
#         filtered_set.append(match.group())
#     else:
#         filtered_set.append('0')
#
# print(filtered_set)


import re

feature_id = "CB008311"
feature_set = 'CB008311-B-'

pattern = r'^{}-[^-]*'.format(re.escape(feature_id))
filtered_set = []

match = re.match(pattern, feature_set)
if match:
    filtered_set.append(match.group())
else:
    filtered_set.append('0')

print(filtered_set)

# myapp/models.py
from django.db import models


class TestCase(models.Model):
    index = models.CharField(max_length=10)
    case_name = models.TextField(max_length=200)
    triggered_by = models.CharField(max_length=100)
    test_result = models.CharField(max_length=100)
    log_link = models.URLField(max_length=100)
    comment = models.TextField(blank=True, null=True)  # 允许为空，以便在初始时没有评论
    date = models.DateField(blank=True, null=True)  # 添加日期字段


def __str__(self):
    return self.case_name

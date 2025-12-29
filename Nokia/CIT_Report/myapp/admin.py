from django.contrib import admin
from .models import TestCase  # 导入你的模型
from django.utils.translation import gettext_lazy as _
import datetime


class DateFilter(admin.SimpleListFilter):
    title = _('date')  # 过滤器的标题
    parameter_name = 'date'  # URL 中的查询参数名称

    def lookups(self, request, model_admin):
        # 返回要显示在过滤器侧边栏中的值和可读性标签的列表
        # 例如，这里可以返回过去一周的日期列表
        date_list = [(datetime.date.today() - datetime.timedelta(days=i), datetime.date.today() - datetime.timedelta(days=i)) for i in range(7)]
        return date_list

    def queryset(self, request, queryset):
        # 根据选择的过滤器选项返回过滤后的查询集
        if self.value():
            return queryset.filter(date=self.value())
        return queryset


# 自定义模型的 admin 界面
class MyModelAdmin(admin.ModelAdmin):
    list_display = ('index', 'case_name', 'triggered_by', 'test_result', 'log_link', 'comment', 'date')  # 在列表页显示的字段
    search_fields = ['index', 'case_name', 'triggered_by', 'test_result', 'log_link', 'comment', 'date']  # 允许搜索的字段
    list_filter = (DateFilter,)  # 添加自定义过滤器


# 使用自定义的 admin 类来注册模型
admin.site.register(TestCase, MyModelAdmin)

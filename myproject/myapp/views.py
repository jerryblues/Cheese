# myapp/views.py
import requests
from . import local_cit_crt_report
from django.shortcuts import render, redirect
from .models import TestCase
import pandas as pd
from .forms import CommentForm
from datetime import datetime, timedelta
import logging


logging.basicConfig(level=logging.INFO,
                    filename='django_local_cit_report.log',
                    filemode='a',
                    format='%(asctime)s - %(levelname)s: %(message)s'
                    )

proxies = {
    "http": "http://10.144.1.10:8080",
    "https": "http://10.144.1.10:8080",
}

i = 0


def get_data_example():
    data = {
        'Index': ['01', '02', '03'],
        'Case_Name': ['CB006457-ET-A-B002_ARP_based_scaling_of_scheduling', 'CB008224-ET-B004_SA_SDL_Band_FDD_Band_Intra_GnB', 'CB008224-ET-A008_Cell_management_5GC000900_5GC000901'],
        'Triggered_By': ['Rui Fang Zhu', 'Yige Zhang', 'Yige Zhang'],
        'Test_Result': ['Failed', 'Passed', 'Passed'],
        'Log_Link': ['http://logs.ute.nsn-rdnet.net/cloud/execution/...', 'http://logs.ute.nsn-rdnet.net/cloud/execution/...', 'http://logs.ute.nsn-rdnet.net/cloud/execution/...']
    }
    return pd.DataFrame(data)


def get_data(date):
    session = requests.Session()
    login_url = 'https://cloud.ute.nsn-rdnet.net/api/v1/auth/login'
    login_data = {'username': 'xxx', 'password': 'xxx'}
    # 发送登录请求
    try:
        response = session.post(login_url, json=login_data, proxies=proxies)
        response.raise_for_status()  # 将触发异常，如果状态码是 4XX 或 5XX
        print("response", response.json())
    except requests.exceptions.HTTPError as errh:
        print("Http Error:", errh)
    except requests.exceptions.ConnectionError as errc:
        print("Error Connecting:", errc)
    except requests.exceptions.Timeout as errt:
        print("Timeout Error:", errt)
    except requests.exceptions.RequestException as err:
        print("OOps: Something Else", err)

    df = local_cit_crt_report.data_summary(session, date)

    # 添加"Index"列，从01开始计数
    df['Index'] = (df.index + 1).astype(str).str.zfill(2)

    # 将"No."列移动到DataFrame的第一列位置
    cols = ['Index'] + [col for col in df.columns if col != 'Index']
    df = df[cols]
    return df


def update_test_cases_from_data_source(date):
    # 检查是否已存在该日期的数据
    if not TestCase.objects.filter(date=date).exists():
        df = get_data(date)  # 获取数据
        # print("df:", df)
        for _, row in df.iterrows():
            TestCase.objects.update_or_create(
                case_name=row['Case_Name'],
                date=date,  # 现在使用日期作为筛选条件之一
                defaults={
                    'index': row['Index'],
                    'triggered_by': row['Triggered_By'],
                    'test_result': row['Test_Result'],
                    'log_link': row['Log_Link'],
                    # 'comment': row.get('Comment', '')  # 如果数据源中有评论信息
                }
            )
        print(f"<-- data for [{date}] has been updated -->")
    else:
        print(f"<-- data for [{date}] already exists -->")


def home(request):
    global i
    i += 1
    print(f'<-- request sent [{i}] times -->')

    # 清空数据库中的旧数据
    # TestCase.objects.all().delete()

    # 生成日期列表
    start_date = datetime(2024, 4, 25)
    end_date = datetime.now()
    delta = timedelta(days=1)
    dates = []

    while end_date >= start_date:
        dates.append(end_date.date())
        end_date -= delta

    selected_date_str = request.GET.get('selected_date')
    if selected_date_str:
        selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        print(f'<-- query data with selected date: [{selected_date}] -->')
        update_test_cases_from_data_source(selected_date)
        # 确保在响应中包含更新后的数据
        test_cases = TestCase.objects.filter(date=selected_date)
    else:
        test_cases = TestCase.objects.none()  # 如果没有选定日期，不显示数据

    # 处理评论保存
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            test_case_id = request.POST.get('case_id')
            case = TestCase.objects.get(id=test_case_id)
            case.comment = form.cleaned_data['comment']
            case.save()
            # 重定向以避免重复提交
            return redirect('home')
    else:
        form = CommentForm()

    # test_cases = TestCase.objects.all()  # 从数据库中读取所有测试案例
    return render(request, 'myapp/home.html', {'dates': dates, 'test_cases': test_cases, 'form': form, 'selected_date_str': selected_date_str})

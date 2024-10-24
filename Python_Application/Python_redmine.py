from redminelib import Redmine
redmine = Redmine('http://redmine.yixinchip.com:8080/', username='zhanghao', password='fantasy0618')
projects = redmine.project.all()
for proj in projects:
    print(proj.name, proj.identifier)

# 获取所有问题
issues = redmine.issue.all()
for issue in issues:
    print(issue.subject, issue.status.name)

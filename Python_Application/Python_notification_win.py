from plyer import notification

def notify_user():
    notification.notify(
        title="info",
        message="new update",
        app_name="GET",
        timeout=None # 通知在x秒后消失
    )

if __name__ == "__main__":
    notify_user()

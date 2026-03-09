import argparse
import json
import time
from typing import Any, Dict, List, Optional

import requests

"""
按时间轴发送 vital-sign MQ 消息（支持多摄像头/多人 results 列表）。

你给的 curl 示例等价于：
POST http://10.1.10.100/vital-sign/vital/signs/sendMq
Headers:
  Authorization: <TOKEN>
  Content-Type: application/json
Body:
  {
    "message_type": 1,
    "task_id": "10@10",
    "timestamp": 1770191590957,
    "results": [
      {"bpm":149,"person_id":"10086","breathe":20,"face_url":"...","img_size":99999}
    ]
  }

本脚本重点：
1) 支持上述格式发送（**一条消息中只有一个 task_id，且只有一组 bpm/breathe**）
2) task_id / timestamp / bpm / img_size 可配置（支持默认值 + 单条覆盖）
3) 按你定义的“相对时间(秒)”定时发送：比如 0s 发A，6s 后发B
4) 用一个列表 SEND_PLAN 方便你直接改配置
"""

# ========================= 基础配置（按需修改） =========================

POST_URL = "http://10.1.10.100/vital-sign/vital/signs/sendMq"

# 直接把 Authorization token 放这里，或运行脚本时通过 --token 传入
AUTH_TOKEN = (
    "eyJhbGciOiJIUzUxMiJ9.eyJhY2NvdW50X2lkIjpudWxsLCJhdXRob3JpemVfaWQiOm51bGwsInVzZXJfaWQi"
    "OiIxIiwicGxpbmsiOm51bGwsInRoaXJkX3VzZXJfaWQiOm51bGwsInVzZXJfa2V5IjoiMTA4NTg3NjItY2Vk"
    "YS00MDI0LWE0NDEtNmVlZmIzNjFjNGZlIiwiZGVwdF9pZF9saXN0IjpudWxsLCJkZXB0X2lkIjpudWxsLCJh"
    "cHBfaWQiOm51bGwsInBsaW5rX2xpc3QiOm51bGwsInVzZXJuYW1lIjoiYWRtaW4iLCJ0ZW5hbnRfY29kZSI6"
    "IkxYX1NYIn0.W4j59Y-XsAZf8upqRxktevGWdfkrbezT17uzkYX_jhy9IwAr4x6MsCodV1kzrwUu-GZm7helGC3Ddxew"
    "4R3bPA"
)

TIMEOUT_S = 10

# 全局默认字段：单条消息未填时，会使用这里的默认值
# task_id 不再写死：可以
#   1) 在 SEND_PLAN 的单条里填（支持简写 A/B）；或
#   2) 运行脚本时通过命令行 --task-id 传入（同样支持 A/B）
DEFAULT_TASK_ID: Optional[str] = None
DEFAULT_MESSAGE_TYPE = 1

# 基准时间戳(毫秒)不再写死：默认取脚本启动时的当前时间戳；
# 如果你想复现某个固定时间戳序列，可用命令行 --base-ts-ms 覆盖
BASE_TIMESTAMP_MS: Optional[int] = None

# person_id 不用配置：始终默认为 10086（即使在配置里写了，也会被覆盖）
DEFAULT_PERSON_ID = "10086"

# task_id 简写映射：为了配置简洁
# A 代表 10@10，B 代表 10@11
TASK_ID_ALIAS: Dict[str, str] = {
    "A": "38@38",
    "B": "38@39",
}

# 单个 result 的默认值（每条消息只有一个 result：一组 bpm/breathe）
DEFAULT_RESULT: Dict[str, Any] = {
    "bpm": 149,
    "breathe": 20,
    "face_url": "https://file.shangjinuu.com/image/face/202509/202509597668.jpg",
    "img_size": 99999,
}

# ========================= 发送计划（你主要改这里） =========================
#
# 规则：
# - at_s: 从脚本开始运行后的第几秒发送
# - task_id: 建议用 A / B，代码会自动映射为真实 task_id
#       A -> 10@10
#       B -> 10@11
# - 每条消息 **只能有一组 bpm/breathe**：
#     - 用 "result": {...} 来配置这一组数据（内部自动组装为 results:[{...}]）
# - result 里你只需要管 bpm 和 img_size，其它字段用默认
#
# 下方是 10 条消息的“模板”，你只要改 at_s / task_id(A/B) / bpm / img_size 即可
SEND_PLAN: List[Dict[str, Any]] = [
    {"at_s": 0,   "task_id": "A", "result": {"bpm": 80,  "img_size": 1500}},
    {"at_s": 6,   "task_id": "A", "result": {"bpm": 81,  "img_size": 1400}},
    {"at_s": 12,  "task_id": "B", "result": {"bpm": 101, "img_size": 1300}},
    {"at_s": 18,  "task_id": "A", "result": {"bpm": 82,  "img_size": 1200}},
    {"at_s": 24,  "task_id": "B", "result": {"bpm": 102, "img_size": 1600}},
    {"at_s": 25,  "task_id": "A", "result": {"bpm": 83,  "img_size": 2000}},
    {"at_s": 26,  "task_id": "B", "result": {"bpm": 103, "img_size": 1500}},
    {"at_s": 32,  "task_id": "A", "result": {"bpm": 84,  "img_size": 1400}},
    {"at_s": 33,  "task_id": "B", "result": {"bpm": 104, "img_size": 1300}},
    {"at_s": 39,  "task_id": "A", "result": {"bpm": 85,  "img_size": 1400}},
    {"at_s": 45,  "task_id": "B", "result": {"bpm": 105, "img_size": 2000}},
    {"at_s": 70,  "task_id": "A", "result": {"bpm": 86,  "img_size": 1000}},
]


def _now_ms() -> int:
    return int(time.time() * 1000)


def _merge_dict(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(base)
    for k, v in override.items():
        if v is not None:
            merged[k] = v
    return merged


def build_payload(
    plan_item: Dict[str, Any],
    *,
    base_timestamp_ms: int,
    default_task_id: Optional[str],
) -> Dict[str, Any]:
    at_s = float(plan_item["at_s"])

    task_id = plan_item.get("task_id") or default_task_id
    # 支持简写 A/B：自动映射为真实 task_id
    if task_id in TASK_ID_ALIAS:
        task_id = TASK_ID_ALIAS[task_id]
    if not task_id:
        raise ValueError("task_id 未配置：请在 SEND_PLAN 单条里填写 task_id，或运行时传 --task-id")
    message_type = plan_item.get("message_type", DEFAULT_MESSAGE_TYPE)

    # timestamp_ms：优先用单条指定的，否则用 base + at_s*1000
    timestamp_ms = plan_item.get("timestamp_ms")
    if timestamp_ms is None:
        timestamp_ms = int(base_timestamp_ms + at_s * 1000)

    # 一条消息只允许 1 个 result（只有一组 bpm/breathe）
    single_result_cfg = plan_item.get("result")
    if not isinstance(single_result_cfg, dict):
        raise ValueError("SEND_PLAN 单条配置必须包含 'result': {...}，且只能有一组 bpm/breathe")

    merged = _merge_dict(DEFAULT_RESULT, single_result_cfg)
    merged["person_id"] = DEFAULT_PERSON_ID  # 强制固定 person_id
    results = [merged]

    return {
        "message_type": message_type,
        "task_id": task_id,
        "timestamp": int(timestamp_ms),
        "results": results,
    }


def send_post(
    session: requests.Session,
    *,
    url: str,
    token: str,
    payload: Dict[str, Any],
    timeout_s: int,
    dry_run: bool,
) -> bool:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = token

    print("\n=== 即将发送 ===")
    print(f"URL: {url}")
    print(f"Headers: {json.dumps(headers, ensure_ascii=False)}")
    print(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")

    if dry_run:
        print("DRY_RUN=1：不实际发送请求")
        return True

    try:
        resp = session.post(url, headers=headers, json=payload, timeout=timeout_s)
        print(f"HTTP {resp.status_code}")
        print(resp.text)
        return resp.status_code == 200
    except Exception as e:
        print(f"请求异常: {e}")
        return False


def run_send_plan(
    plan: List[Dict[str, Any]],
    *,
    url: str,
    token: str,
    base_timestamp_ms: int,
    default_task_id: Optional[str],
    timeout_s: int,
    dry_run: bool,
) -> None:
    if not plan:
        print("SEND_PLAN 为空，无事可做")
        return

    # 按 at_s 排序，保证执行顺序正确
    plan_sorted = sorted(plan, key=lambda x: float(x["at_s"]))

    start_monotonic = time.monotonic()
    start_wall_ms = _now_ms()

    print("=== 开始按时间轴发送 ===")
    print(f"Start wall-clock ms: {start_wall_ms}")
    print(f"Base timestamp ms: {base_timestamp_ms}")
    print(f"Total items: {len(plan_sorted)}")

    with requests.Session() as session:
        for idx, item in enumerate(plan_sorted, start=1):
            at_s = float(item["at_s"])
            due = start_monotonic + at_s
            sleep_s = due - time.monotonic()
            if sleep_s > 0:
                time.sleep(sleep_s)

            payload = build_payload(
                item,
                base_timestamp_ms=base_timestamp_ms,
                default_task_id=default_task_id,
            )
            ok = send_post(
                session,
                url=url,
                token=token,
                payload=payload,
                timeout_s=timeout_s,
                dry_run=dry_run,
            )
            print(f"[{idx}/{len(plan_sorted)}] at_s={at_s} 发送{'成功' if ok else '失败'}")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="按时间轴发送 vital-sign MQ 消息（message_type=1 等）")
    p.add_argument("--url", default=POST_URL, help="发送接口 URL")
    p.add_argument("--token", default=AUTH_TOKEN, help="Authorization token（不填则不带该头）")
    p.add_argument(
        "--task-id",
        default=DEFAULT_TASK_ID,
        help="默认 task_id（SEND_PLAN 单条未写 task_id 时使用）",
    )
    p.add_argument(
        "--base-ts-ms",
        type=int,
        default=BASE_TIMESTAMP_MS,
        help="基准 timestamp(毫秒)，不填则取脚本启动时当前时间戳",
    )
    p.add_argument("--timeout", type=int, default=TIMEOUT_S, help="HTTP 超时(秒)")
    p.add_argument("--dry-run", action="store_true", help="只打印不发送")
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()

    runtime_base_ts_ms = args.base_ts_ms if args.base_ts_ms is not None else _now_ms()
    run_send_plan(
        SEND_PLAN,
        url=args.url,
        token=args.token,
        base_timestamp_ms=runtime_base_ts_ms,
        default_task_id=args.task_id,
        timeout_s=args.timeout,
        dry_run=args.dry_run,
    )

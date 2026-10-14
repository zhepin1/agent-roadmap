# -*- coding: utf-8 -*-
"""W1D4 练习（W2D2 重构版）：用 httpx 调公开天气 API，把返回的 JSON 解析后存进 SQLite。

对应今日语法点：typing 类型标注 + dataclass 数据类。
不用 Key、完全免费的数据源：Open-Meteo（open-meteo.com）。
"""

from dataclasses import dataclass  # 用 @dataclass 把"一条天气记录"定义成清晰的数据结构
from datetime import datetime, timezone  # 标准库，记录"抓取时间"
from typing import Any  # Any = 任意类型，用于"值类型不固定"的场景

import logging  # 标准库，记录日志（替代 print）
import httpx  # 第三方库，需要先 pip install httpx；比标准库 urllib 好用，后面还会用它做并发
import sqlite3  # Python 自带，操作 SQLite 数据库
import json  # 标准库，把 dict 转成字符串存进数据库

# 日志配置：带时间 + 级别，比 print 专业；__name__ 是当前模块名（week01.fetch_weather）
logging.basicConfig(
    level=logging.INFO,  # 低于 INFO 的不显示（可改成 WARNING 试试看效果）
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


# ---- 配置区：改这里就能换城市 / 参数 ----
# 给常量也标类型，编辑器/ruff 都能帮你检查
API_URL: str = "https://api.open-meteo.com/v1/forecast"
PARAMS: dict[str, Any] = {
    "latitude": 39.9042,  # 北京纬度
    "longitude": 116.4074,  # 北京经度
    "current": "temperature_2m,relative_humidity_2m,wind_speed_10m",  # 要哪些实时字段
    "timezone": "Asia/Shanghai",
}
DB_PATH: str = "weather.db"  # 数据库文件名（运行后自动生成）


# @dataclass：一行顶替"手写 __init__ + 一堆属性"。下面这个类就是"一条天气记录"的模板
@dataclass
class WeatherRecord:
    """一条天气记录的结构化定义：字段 + 类型一目了然。"""

    city: str
    fetched_at: str
    temperature: float
    humidity: float
    wind_speed: float
    raw: str


def fetch_weather() -> dict[str, Any]:
    """发 GET 请求，拿回天气数据（dict 形式）。

    返回类型标注 -> dict[str, Any]：返回的是一个字典。
    """
    # httpx.get 发请求；params 会自动拼成 ?latitude=...&longitude=...
    resp = httpx.get(API_URL, params=PARAMS, timeout=10)
    # 如果返回状态码不是 2xx（比如 404/500），这里会直接抛异常，避免拿到错误数据还继续
    resp.raise_for_status()
    # .json() 把返回的文本（JSON 格式）解析成 Python 的 dict / list
    return resp.json()


def save_to_db(record: WeatherRecord) -> None:
    """把一条天气记录存进 SQLite。

    参数标注 record: WeatherRecord，说明"这个函数只接受 WeatherRecord 类型"。
    返回标注 -> None，说明"它不返回任何东西"（只负责存）。
    """
    # 连接数据库（文件不存在会自动创建）
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        # 建表：IF NOT EXISTS 保证重复运行不会报错
        cur.execute("""
            CREATE TABLE IF NOT EXISTS weather (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                city         TEXT,
                fetched_at   TEXT,
                temperature  REAL,
                humidity     REAL,
                wind_speed   REAL,
                raw          TEXT
            )
        """)
        # 插入一条记录；用 ? 占位符防止 SQL 注入（好习惯，以后写 Agent 也别直接拼字符串）
        cur.execute(
            """
            INSERT INTO weather (city, fetched_at, temperature, humidity, wind_speed, raw)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                record.city,  # dataclass 用法：record.city 而不是 record["city"]
                record.fetched_at,
                record.temperature,
                record.humidity,
                record.wind_speed,
                record.raw,
            ),
        )
        conn.commit()  # 提交事务，数据才真正写入
    finally:
        conn.close()  # 不管成功失败都关掉连接，释放资源


def main() -> None:
    """程序入口：抓数据 → 组装成 WeatherRecord → 存库 → 记录日志。"""
    try:
        data: dict[str, Any] = fetch_weather()  # 1) 抓数据
        current: dict[str, Any] = data["current"]  # 2) 从嵌套 dict 里取到"当前天气"那一层
        # 3) 用 WeatherRecord(...) 组装，而不是手写一个普通 dict —— 类型清晰、不易写错字段名
        record = WeatherRecord(
            city="北京",
            fetched_at=datetime.now(timezone.utc).isoformat(),
            temperature=current["temperature_2m"],
            humidity=current["relative_humidity_2m"],
            wind_speed=current["wind_speed_10m"],
            raw=json.dumps(data, ensure_ascii=False),  # 原始 JSON 存一份，方便以后查
        )
        # 非致命提醒：温度超出合理范围时记 warning（不中断程序）
        if not (-60 <= record.temperature <= 60):
            logger.warning(f"温度异常 {record.temperature} °C，可能是数据错误")
        save_to_db(record)  # 4) 存数据库
        # 5) 用 logger 记录结果（info = 正常运行信息）
        logger.info(f"已保存 {record.city} 的天气：")
        logger.info(f"  温度 {record.temperature} °C")
        logger.info(f"  湿度 {record.humidity} %")
        logger.info(f"  风速 {record.wind_speed} km/h")
        logger.info(f"  抓取时间 {record.fetched_at}")
    except KeyError as e:
        # error = 出错了：返回的数据结构和预期不符
        logger.error(f"返回数据缺少字段：{e}")
    except Exception as e:
        # error = 出错了：抓数据或存库失败
        logger.error(f"抓天气失败：{e}")


if __name__ == "__main__":
    main()

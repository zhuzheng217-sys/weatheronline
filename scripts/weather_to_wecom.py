#!/usr/bin/env python3
"""Fetch weather forecast from Open-Meteo and push to WeCom robot webhook."""

from __future__ import annotations

import datetime as dt
import json
import os
import sys
import urllib.parse
import urllib.request

WEATHER_CODE_MAP = {
    0: "晴",
    1: "大部晴朗",
    2: "局部多云",
    3: "阴",
    45: "雾",
    48: "冻雾",
    51: "小毛毛雨",
    53: "毛毛雨",
    55: "大毛毛雨",
    56: "小冻毛毛雨",
    57: "大冻毛毛雨",
    61: "小雨",
    63: "中雨",
    65: "大雨",
    66: "小冻雨",
    67: "大冻雨",
    71: "小雪",
    73: "中雪",
    75: "大雪",
    77: "冰粒",
    80: "阵雨",
    81: "中等阵雨",
    82: "强阵雨",
    85: "阵雪",
    86: "强阵雪",
    95: "雷暴",
    96: "雷暴伴小冰雹",
    99: "雷暴伴大冰雹",
}


def http_get_json(url: str, timeout: int = 15) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "weatheronline-bot/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
        return json.loads(resp.read().decode("utf-8"))


def http_post_json(url: str, payload: dict, timeout: int = 15) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "User-Agent": "weatheronline-bot/1.0"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
        return json.loads(resp.read().decode("utf-8"))


def get_coordinates(city: str) -> tuple[float, float, str]:
    params = urllib.parse.urlencode({"name": city, "count": 1, "language": "zh", "format": "json"})
    url = f"https://geocoding-api.open-meteo.com/v1/search?{params}"
    data = http_get_json(url)
    results = data.get("results") or []
    if not results:
        raise RuntimeError(f"未找到城市：{city}")
    first = results[0]
    display_name = ", ".join(
        [x for x in [first.get("name"), first.get("admin1"), first.get("country")] if x]
    )
    return float(first["latitude"]), float(first["longitude"]), display_name


def weather_text(code: int) -> str:
    return WEATHER_CODE_MAP.get(code, f"未知天气({code})")


def get_forecast(lat: float, lon: float, timezone: str, days: int = 2) -> dict:
    params = urllib.parse.urlencode(
        {
            "latitude": lat,
            "longitude": lon,
            "daily": "weathercode,temperature_2m_max,temperature_2m_min,precipitation_probability_max,sunrise,sunset",
            "forecast_days": days,
            "timezone": timezone,
        }
    )
    url = f"https://api.open-meteo.com/v1/forecast?{params}"
    return http_get_json(url)


def build_markdown(city_display: str, forecast: dict, timezone: str) -> str:
    daily = forecast["daily"]
    lines = [f"## 🌤 每日天气预报（{city_display}）", ""]

    today = dt.datetime.now().strftime("%Y-%m-%d")
    lines.append(f"> 生成时间：{today}（时区：{timezone}）")
    lines.append("")

    for i, date in enumerate(daily["time"]):
        code = int(daily["weathercode"][i])
        t_max = daily["temperature_2m_max"][i]
        t_min = daily["temperature_2m_min"][i]
        rain_prob = daily["precipitation_probability_max"][i]
        sunrise = daily["sunrise"][i].split("T")[-1]
        sunset = daily["sunset"][i].split("T")[-1]
        lines.append(f"### {date}")
        lines.append(
            f"- 天气：**{weather_text(code)}**  \n- 气温：**{t_min}°C ~ {t_max}°C**"
            f"  \n- 降水概率：**{rain_prob}%**  \n- 日出/日落：{sunrise} / {sunset}"
        )
        lines.append("")

    lines.append("---")
    lines.append("数据来源：Open-Meteo（免费 API）")
    return "\n".join(lines)


def send_to_wecom(webhook_key: str, content: str) -> None:
    webhook = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={webhook_key}"
    payload = {
        "msgtype": "markdown",
        "markdown": {"content": content},
    }
    resp = http_post_json(webhook, payload)
    if resp.get("errcode") != 0:
        raise RuntimeError(f"企业微信推送失败: {resp}")


def main() -> int:
    webhook_key = os.getenv("WECOM_WEBHOOK_KEY", "").strip()
    if not webhook_key:
        print("缺少 WECOM_WEBHOOK_KEY 环境变量", file=sys.stderr)
        return 1

    city = os.getenv("CITY", "宣城").strip()
    timezone = os.getenv("TIMEZONE", "Asia/Shanghai").strip()

    lat = os.getenv("LAT", "").strip()
    lon = os.getenv("LON", "").strip()

    if lat and lon:
        latitude, longitude = float(lat), float(lon)
        city_display = f"{city} ({latitude}, {longitude})"
    else:
        latitude, longitude, city_display = get_coordinates(city)

    forecast = get_forecast(latitude, longitude, timezone, days=2)
    content = build_markdown(city_display, forecast, timezone)
    send_to_wecom(webhook_key, content)

    print(f"推送成功：{city_display}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

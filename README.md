# WeatherOnline（GitHub Actions + 企业微信天气推送）

这是一个**免费**的天气预报自动推送服务：
- 使用 GitHub Actions 定时运行。
- 使用 Open-Meteo 免费 API 获取天气预报。
- 将结果推送到企业微信机器人。

## 1. 准备企业微信群机器人

1. 在企业微信群中添加机器人。
2. 复制 webhook 地址，例如：
   `https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxxxxxxx`
3. 只保留 `key` 的值（上例中的 `xxxxxxxx`）。

## 2. 配置 GitHub Secrets / Variables

进入仓库 **Settings → Secrets and variables → Actions**，设置：

### Secrets
- `WECOM_WEBHOOK_KEY`（必填）：企业微信机器人 webhook 的 key。

### Variables（可选）
- `CITY`：城市名（默认 `宣城`）。
- `TIMEZONE`：时区（默认 `Asia/Shanghai`）。
- `LAT`：纬度（如果设置了 `LAT` + `LON`，将优先使用坐标，不再按城市名解析）。
- `LON`：经度。

## 3. 定时任务说明

工作流文件：`.github/workflows/weather-push.yml`

- 每天北京时间 07:00 自动推送（cron: `0 23 * * *`，GitHub Actions 使用 UTC）。
- 支持手动触发（`workflow_dispatch`）。

## 4. 本地调试

```bash
export WECOM_WEBHOOK_KEY='你的key'
export CITY='宣城'
python scripts/weather_to_wecom.py
```

## 5. 测试方式

### 5.1 本地测试（推荐先做）

```bash
# 1) 必填：企业微信机器人 key
export WECOM_WEBHOOK_KEY='你的key'

# 2) 可选：默认已是宣城，不填也可
export CITY='宣城'
export TIMEZONE='Asia/Shanghai'

# 3) 运行
python scripts/weather_to_wecom.py
```

预期结果：
- 控制台输出 `推送成功：...`。
- 企业微信群收到 Markdown 天气预报消息。

### 5.2 GitHub Actions 手动测试

1. 进入仓库 **Actions** 页面。
2. 选择工作流 **Daily Weather to WeCom**。
3. 点击 **Run workflow** 手动触发。
4. 检查日志中 `Push weather forecast` 步骤是否成功。
5. 验证企业微信群是否收到消息。

### 5.3 定时任务验证

- 工作流设置为每天北京时间 07:00 自动执行（UTC 23:00）。
- 次日查看 Actions 历史运行记录和企业微信群消息即可验证。

## 6. 费用说明

- GitHub Actions：公开仓库免费额度通常足够本场景。
- Open-Meteo API：免费使用。
- 企业微信机器人：企业微信能力范围内免费。

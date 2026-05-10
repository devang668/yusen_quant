# 加密货币量化交易自学手册

> 目标：利用开源项目快速入门，建立自己的量化交易系统
> 背景：通信工程 / Python / C++ / 有自己的项目积累

---

## 痛点对照

在开始之前，先明确你目前遇到的三个核心问题：

| 痛点 | 对应章节 | 解决方案 |
|:---|:---|:---|
| 代码散乱，难以维护 | [第二章：架构设计](#二架构设计) | 事件驱动四层解耦 |
| 找开源项目像大海捞针 | [第三章：优质项目清单](#三优质开源项目清单) | 按需求精准定位 |
| 网络不稳，API 常断连 | [第四章：网络与部署方案](#四网络与部署方案) | VPS / 代码级代理 |

---

## 一、为什么靠开源项目入门是最高效的

1. **跳过重复造轮子** — CCXT 已经解决了 100+ 交易所 API 归一化问题
2. **真实代码可参考** — 成熟框架的架构设计是经过实盘验证的
3. **圈子资源丰富** — 很多量化工作室会开源部分策略，站在前人肩膀上事半功倍
4. **先跑通再深入** — 先让系统跑起来，再研究底层原理

---

## 二、架构设计：如何让代码从"散乱"变"模块化"

这是很多人自研量化系统的必经之路。代码"散乱"的本质是**把不同职责的代码混在了一起**。

### 四层解耦架构

成熟的量化系统分为四个独立模块，互不依赖：

```
┌─────────────────────────────────────────────────────┐
│                   Data Handler                      │
│  职责：抓取数据、格式化、自动重连                    │
│  特点：只和数据源打交道，不涉及任何交易逻辑          │
└─────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│                 Strategy Engine                     │
│  职责：接收数据 → 计算指标 → 输出信号                │
│  特点：纯数学逻辑，单元测试友好                      │
└─────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│               Portfolio Manager                     │
│  职责：仓位计算、止损、风控                          │
│  特点：所有"钱相关"的逻辑在这里                       │
└─────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│               Execution Handler                     │
│  职责：发单、追单、成交回报处理                      │
│  特点：只和交易所 API 打交道                          │
└─────────────────────────────────────────────────────┘
```

### 自检标准

如果你的策略代码里出现了 `ccxt.create_order`，说明架构有问题。正确的做法：

```python
# ❌ 错误：逻辑散乱
class MyStrategy:
    def on_tick(self, ticker):
        if self.compute_signal(ticker) > threshold:
            exchange.create_order(...)  # 策略里直接调用了交易所API

# ✅ 正确：职责分离
class MyStrategy:
    def on_tick(self, ticker) -> Signal:
        return Signal(self.compute_signal(ticker))  # 只返回信号，不下单

# Execution Handler 负责：
class ExecutionHandler:
    def execute(self, signal: Signal, portfolio: Portfolio):
        exchange.create_order(...)  # 只有这里调用交易所API
```

### 日志规范（放弃 print）

```python
import logging

# 创建专用 logger
logger = logging.getLogger('quant.data')
order_logger = logging.getLogger('quant.order')

# 不同信息进不同文件
fh = logging.FileHandler('logs/market_data.log')
fh.setLevel(logging.DEBUG)
order_logger.addHandler(fh)

order_logger.info(f"买单成交 | 价格:{price} | 数量:{amount}")
```

---

## 三、优质开源项目清单

### 3.1 必学基础框架

#### CCXT — 交易所通信层（必学）

所有项目的底层依赖，支持 100+ 交易所统一接口。

```python
import ccxt

binance = ccxt.binance({
    'apiKey': 'YOUR_API_KEY',
    'secret': 'YOUR_SECRET',
    'enableRateLimit': True,
    'options': {'defaultType': 'spot'},  # 现货
})

# 获取 K 线
ohlcv = binance.fetch_ohlcv('BTC/USDT', '1h', limit=100)

# 获取深度图
orderbook = binance.fetch_order_book('BTC/USDT')
```

#### VN.py — 国内量化首选（C++ 核心）

国内最成熟的量化框架，底层 C++ 高性能，深度适配币安 / OKX / Bybit。

- GitHub: https://github.com/vnpy/vnpy
- 特点：国产、社区活跃、文档中文友好

#### Freqtrade — 策略入门首选

最火的 Python 交易机器人，回测 + 优化 + 实盘一条龙。

```bash
git clone https://github.com/freqtrade/freqtrade.git
cd freqtrade
python -m venv venv
pip install -e.

# 下载历史数据
freqtrade download-data --pairs BTC/USDT --timeframe 1h

# 回测
freqtrade backtesting --config config.json --strategy DefaultStrategy

# 实盘
freqtrade trade --config config.json --strategy DefaultStrategy
```

---

### 3.2 C++ 硬核项目（适合构建高性能底座）

#### WonderTrader — 国产 C++ 硬核框架

最适合有 C++ 背景的开发者，高性能、多策略并发。

- GitHub: https://github.com/wondertrader/wondertrader
- 特点：C++ 核心 / Python 调用 / 高频低延迟 / 插件化架构

#### Hikyuu Quant Framework — 金融级架构

代码组织极其严密，适合学习"如何把金融工程思维融入代码架构"。

- GitHub: https://github.com/fanyf2002/hikyuu

#### QuantConnect Lean Engine — 世界级架构

全球最著名的开源量化引擎，架构设计堪称教科书。

- GitHub: https://github.com/QuantConnect/Lean
- 特点：C# 核心 / 支持 Python / 架构极其严谨

---

### 3.3 按需求选择

| 需求场景 | 推荐项目 | 理由 |
|:---|:---|:---|
| **快速跑通一个策略** | Freqtrade | 安装简单，文档完善 |
| **做市 / 套利** | Hummingbot | 专为做市设计 |
| **高频回测** | VectorBT | 向量化回测，速度极快 |
| **机器学习策略** | Freqtrade + FreqAI | 内置 ML 支持 |
| **C++ 高性能底座** | WonderTrader | 国产硬核 |
| **学习架构设计** | QuantConnect Lean | 世界级参考 |
| **国内 + Python** | VN.py | 社区活跃，中文友好 |

---

### 3.4 更多可参考的项目

| 项目 | 链接 | 特点 |
|:---|:---|:---|
| CCXT | https://github.com/ccxt/ccxt | 交易所统一接口 |
| Hummingbot | https://github.com/hummingbot/hummingbot | 做市策略专家 |
| VectorBT | https://github.com/polakowo/vectorbt | 超高速回测 |
| FreqAI | 内置于 Freqtrade | ML 增强策略 |
| Flashbots | https://github.com/flashbots | 以太坊 MEV 套利 |

### GitHub Topics（找项目用）
- https://github.com/topics/crypto-trading-bot
- https://github.com/topics/quantitative-trading
- https://github.com/topics/algorithmic-trading

---

## 四、网络与部署方案

这是你提到的一个关键痛点：本地需要挂着梯子才能访问交易所 API，极其不稳定。

### 方案一：租用海外 VPS（推荐）

把代码部署到海外服务器，服务器本身直连交易所，延迟低且稳定。

```bash
# 推荐配置（最便宜的即可）
# AWS 东京 / 新加坡节点
# 阿里云国际版（香港节点）
# 腾讯云海外版

# 部署结构
# 本地  →  SSH  →  海外 VPS  →  交易所 API
#         (跳板)     (代码运行)
```

**优点：**
- 服务器在海外，直连交易所毫秒级
- 完全不需要梯子
- 断网不影响 VPS 上的运行

**缺点：**
- 有费用（约 20-50 元/月）
- 调试不如本地方便

### 方案二：代码级代理（调试用）

如果必须本地调试，在 CCXT 初始化时注入代理：

```python
import ccxt

binance = ccxt.binance({
    'apiKey': 'YOUR_API_KEY',
    'secret': 'YOUR_SECRET',
    'proxies': {
        'http': 'http://127.0.0.1:7890',      # 你的梯子端口
        'https': 'http://127.0.0.1:7890',
    },
})
```

### 方案三：反向代理（Nginx）

在 VPS 上搭一个 Nginx 反向代理，本地代码访问 VPS IP，由服务器转发到交易所：

```nginx
# /etc/nginx/conf.d/crypto-proxy.conf
server {
    listen 8080;
    location /binance/ {
        proxy_pass https://api.binance.com/;
        proxy_set_header Host api.binance.com;
    }
}
```

---

## 五、自检清单

完成以下事项，说明你的系统已经初步成型：

- [ ] **架构分离** — 策略逻辑和交易所 API 调用不在同一个文件
- [ ] **日志系统** — 行情数据、下单回报、网络错误分别记录到不同文件
- [ ] **单元测试** — 指标计算函数有 `pytest` 测试，输入一致输出必一致
- [ ] **回测验证** — 策略在历史数据上跑通，且做了样本外验证
- [ ] **参数不过拟合** — 用 walk-forward 验证，而非过度优化

---

## 六、快速入门路线图

```
第1周：CCXT 入门
  ├── 学会获取 K 线 / Order Book
  ├── WebSocket 订阅实时行情
  └── 理解限流机制

第2-3周：Freqtrade 实战
  ├── 跑通自带的示例策略
  ├── 修改 MACD / RSI 策略
  └── 学会用 hyperopt 优化参数

第4周：架构重构
  ├── 把散乱的代码按四层架构拆分
  ├── 引入 logging 日志系统
  └── 给核心函数写单元测试

第5周：部署上线
  ├── 选一个海外 VPS 部署
  ├── 配置自动重启（supervisor / systemd）
  └── 接入 Telegram 通知

第6周+：策略深化
  ├── 研究别人的开源策略（Freqtrade Strategies 仓库）
  ├── 学习仓位管理和风控
  └── 逐步加入自己的策略想法
```

---

## 七、避坑指南

1. **不要迷信复杂模型** — 简单的波动率策略 / 趋势跟踪往往比深度学习更健壮
2. **永远设止损** — 币圈波动极大，不设止损可能归零
3. **注意 API Key 安全** — 环境变量读取，不要明文写在代码里
4. **手续费和滑点** — 回测时务必计入，实盘利润可能和回测差很远
5. **过拟合问题** — 样本外测试不通过，策略不要上实盘

---

准备好开始了吗？建议从 **Freqtrade 跑通第一个策略** 开始，有问题随时问我。

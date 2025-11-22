# IP池使用说明

## 功能概述

为了防止请求过多被封禁以及防爬虫，项目已经集成了IP池功能，支持代理IP轮换。系统会根据不同的数据源使用不同的代理池，提高请求成功率和稳定性。

## 核心特性

- **多代理池支持**：为不同数据源（地铁、安居客、Firecrawl API）配置独立的代理池
- **智能轮换**：自动检测代理IP可用性，轮换使用可用代理
- **失败重试**：支持请求失败后的自动重试机制
- **状态监控**：实时监控代理IP的使用状态和成功率
- **灵活配置**：通过环境变量灵活配置代理IP和参数

## 文件结构

### 核心模块
- `src/subway_visualize/services/proxy_pool.py` - IP池管理核心模块
- `src/subway_visualize/services/subway_visualize.py` - 地铁数据服务（已集成IP池）
- `src/subway_visualize/services/crawler_firecrawl.py` - Firecrawl爬虫服务（已集成IP池）
- `src/subway_visualize/config.py` - 配置文件（已添加IP池配置）

### 启动文件
- `src/subway_visualize/main.py` - 主应用启动文件（已集成IP池初始化）
- `serve.py` - 服务启动文件（已集成IP池初始化）

### 配置和测试
- `.env.example` - 环境变量配置示例
- `test_proxy_pools.py` - IP池功能测试脚本

## 配置方法

### 1. 环境变量配置

复制 `.env.example` 为 `.env`，然后根据需要配置代理IP：

```bash
# 地铁数据代理池（最多支持19个代理）
SUBWAY_PROXY_1=http://user:pass@proxy1.example.com:8080
SUBWAY_PROXY_2=http://user:pass@proxy2.example.com:8080
SUBWAY_PROXY_MAX_FAILURES=3
SUBWAY_PROXY_FAILURE_TIMEOUT=300
SUBWAY_PROXY_TEST_URL=https://map.amap.com/service/subway

# 安居客数据代理池
ANJUKE_PROXY_1=http://user:pass@proxy3.example.com:8080
ANJUKE_PROXY_2=http://user:pass@proxy4.example.com:8080
ANJUKE_PROXY_MAX_FAILURES=3
ANJUKE_PROXY_FAILURE_TIMEOUT=300
ANJUKE_PROXY_TEST_URL=https://bj.zu.anjuke.com/ditie/

# Firecrawl API代理池
FIRECRAWL_PROXY_1=http://user:pass@proxy5.example.com:8080
FIRECRAWL_PROXY_2=http://user:pass@proxy6.example.com:8080
FIRECRAWL_PROXY_MAX_FAILURES=3
FIRECRAWL_PROXY_FAILURE_TIMEOUT=300
FIRECRAWL_PROXY_TEST_URL=https://api.firecrawl.dev
```

### 2. 代理IP格式

支持以下代理格式：
- `http://proxy.example.com:8080`
- `http://user:password@proxy.example.com:8080`
- `https://proxy.example.com:8080`
- `socks5://proxy.example.com:1080`

### 3. 配置参数说明

- `*_PROXY_MAX_FAILURES`：单个代理IP的最大失败次数，超过后将被标记为不可用
- `*_PROXY_FAILURE_TIMEOUT`：代理IP被封禁后的冷却时间（秒）
- `*_PROXY_TEST_URL`：用于测试代理IP可用性的目标URL

## 使用方法

### 1. 在代码中使用IP池

```python
from subway_visualize.services.proxy_pool import safe_request

# 使用特定IP池发送请求
response = safe_request(
    url='https://example.com',
    pool_name='subway',  # 使用地铁数据代理池
    max_retries=3,       # 最大重试次数
    retry_delay=0.6      # 重试间隔（秒）
)

# 获取代理会话（高级用法）
from subway_visualize.services.proxy_pool import get_proxy_session

session = get_proxy_session(pool_name='anjuke')
response = session.get('https://example.com')
```

### 2. 支持的IP池名称

- `subway` - 地铁数据代理池
- `anjuke` - 安居客数据代理池  
- `firecrawl` - Firecrawl API代理池

### 3. 请求参数

`safe_request` 函数支持以下参数：

- `url`：目标URL（必需）
- `method`：请求方法，默认 'GET'
- `pool_name`：IP池名称，默认 None（使用本地网络）
- `max_retries`：最大重试次数，默认 3
- `retry_delay`：重试间隔（秒），默认 1.0
- `**kwargs`：其他 requests 库支持的参数

## 测试和监控

### 1. 运行测试

```bash
# 测试IP池功能
python test_proxy_pools.py
```

测试脚本会：
- 检查配置的代理IP池
- 测试每个代理的可用性
- 验证HTTP请求功能
- 测试特定网站的访问

### 2. 监控代理状态

在应用运行期间，系统会自动：
- 记录每个代理IP的使用情况
- 监控成功率和失败次数
- 自动轮换到可用代理
- 在代理被封禁时进行冷却处理

## 故障排查

### 1. 代理IP无效

- 检查代理IP格式是否正确
- 验证代理IP是否需要认证
- 测试代理IP是否可用（使用curl或其他工具）
- 检查网络连接是否正常

### 2. 请求仍然被封禁

- 增加 `max_retries` 参数值
- 增加 `retry_delay` 间隔时间
- 添加更多代理IP到池中
- 检查目标网站的反爬虫策略

### 3. 性能问题

- 减少重试次数
- 减少重试间隔时间
- 使用更高质量的代理IP
- 考虑使用专业代理服务

### 4. 日志调试

系统会记录详细的请求日志，包括：
- 使用的代理IP
- 请求URL和参数
- 成功/失败状态
- 错误信息

查看日志可以帮助诊断问题。

## 最佳实践

1. **合理配置重试次数**：不要设置过高的重试次数，避免长时间等待
2. **适当设置重试间隔**：给目标网站足够的响应时间
3. **定期检查代理IP**：定期测试代理IP的可用性
4. **监控代理池状态**：关注代理池的使用情况和成功率
5. **备用方案**：准备本地网络作为备用方案

## 注意事项

- 使用代理IP可能违反某些网站的服务条款，请确保合规使用
- 免费代理IP通常不稳定，建议使用付费的高质量代理服务
- 定期检查代理IP的有效性，及时更新失效的代理
- 合理设置请求频率，避免对目标网站造成过大压力

## 更新日志

- 2024-11-22：初始版本，集成IP池功能
- 支持地铁、安居客、Firecrawl三个独立代理池
- 实现智能轮换和失败重试机制
- 添加完整的配置和测试功能
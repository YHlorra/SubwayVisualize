import os
from typing import Dict, Any

def _root_dir() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _read_dotenv() -> Dict[str, str]:
    env_path = os.path.join(_root_dir(), '.env')
    out: Dict[str, str] = {}
    if not os.path.exists(env_path):
        return out
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                s = line.strip()
                if not s or s.startswith('#'):
                    continue
                if '=' in s:
                    k, v = s.split('=', 1)
                    out[k.strip()] = v.strip()
    except Exception:
        return {}
    return out

def _get(key: str, default: str = '') -> str:
    env_file = _read_dotenv()
    return os.environ.get(key) or env_file.get(key) or default


def get_firecrawl_settings() -> Dict[str, Any]:
    key = _get('FIRECRAWL_API_KEY')
    base = _get('FIRECRAWL_API_BASE', 'https://api.firecrawl.dev/v2')
    timeout = int(_get('FIRECRAWL_TIMEOUT', '30') or '30')
    enabled = bool(key)
    return {
        'enabled': enabled,
        'key': key,
        'base': base,
        'timeout': timeout,
    }

def get_proxy_pools_config() -> Dict[str, Any]:
    proxy_config = {}
    
    # 地铁数据IP池配置
    subway_proxies = []
    for i in range(1, 20):  # 支持最多19个代理
        proxy = _get(f'SUBWAY_PROXY_{i}')
        if proxy:
            subway_proxies.append(proxy)
    
    if subway_proxies:
        proxy_config['subway'] = {
            'proxies': subway_proxies,
            'max_failures': int(_get('SUBWAY_PROXY_MAX_FAILURES', '3') or '3'),
            'failure_timeout': int(_get('SUBWAY_PROXY_FAILURE_TIMEOUT', '3600') or '3600'),
            'test_url': _get('SUBWAY_PROXY_TEST_URL', 'https://httpbin.org/ip')
        }
    
    # 安居客数据IP池配置
    anjuke_proxies = []
    for i in range(1, 20):  # 支持最多19个代理
        proxy = _get(f'ANJUKE_PROXY_{i}')
        if proxy:
            anjuke_proxies.append(proxy)
    
    if anjuke_proxies:
        proxy_config['anjuke'] = {
            'proxies': anjuke_proxies,
            'max_failures': int(_get('ANJUKE_PROXY_MAX_FAILURES', '3') or '3'),
            'failure_timeout': int(_get('ANJUKE_PROXY_FAILURE_TIMEOUT', '3600') or '3600'),
            'test_url': _get('ANJUKE_PROXY_TEST_URL', 'https://httpbin.org/ip')
        }
    
    # Firecrawl API IP池配置
    firecrawl_proxies = []
    for i in range(1, 20):  # 支持最多19个代理
        proxy = _get(f'FIRECRAWL_PROXY_{i}')
        if proxy:
            firecrawl_proxies.append(proxy)
    
    if firecrawl_proxies:
        proxy_config['firecrawl'] = {
            'proxies': firecrawl_proxies,
            'max_failures': int(_get('FIRECRAWL_PROXY_MAX_FAILURES', '3') or '3'),
            'failure_timeout': int(_get('FIRECRAWL_PROXY_FAILURE_TIMEOUT', '3600') or '3600'),
            'test_url': _get('FIRECRAWL_PROXY_TEST_URL', 'https://httpbin.org/ip')
        }
    
    return proxy_config

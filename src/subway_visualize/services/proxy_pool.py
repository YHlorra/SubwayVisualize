import random
import time
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import requests
from threading import Lock

logger = logging.getLogger(__name__)

class ProxyPool:
    def __init__(self, proxies: List[str] = None, max_failures: int = 3, 
                 failure_timeout: int = 3600, test_url: str = 'https://httpbin.org/ip'):
        self.proxies = proxies or []
        self.max_failures = max_failures
        self.failure_timeout = failure_timeout
        self.test_url = test_url
        self.proxy_stats: Dict[str, Dict] = {}
        self.current_index = 0
        self.lock = Lock()
        self._initialize_stats()
    
    def _initialize_stats(self):
        for proxy in self.proxies:
            self.proxy_stats[proxy] = {
                'failures': 0,
                'last_failure': None,
                'successes': 0,
                'last_success': None,
                'is_banned': False,
                'ban_time': None
            }
    
    def add_proxy(self, proxy: str):
        if proxy not in self.proxies:
            self.proxies.append(proxy)
            self.proxy_stats[proxy] = {
                'failures': 0,
                'last_failure': None,
                'successes': 0,
                'last_success': None,
                'is_banned': False,
                'ban_time': None
            }
    
    def remove_proxy(self, proxy: str):
        if proxy in self.proxies:
            self.proxies.remove(proxy)
            self.proxy_stats.pop(proxy, None)
    
    def _is_proxy_available(self, proxy: str) -> bool:
        stats = self.proxy_stats.get(proxy, {})
        
        if stats.get('is_banned'):
            ban_time = stats.get('ban_time')
            if ban_time and (datetime.now() - ban_time).seconds < self.failure_timeout:
                return False
            else:
                stats['is_banned'] = False
                stats['ban_time'] = None
        
        if stats['failures'] >= self.max_failures:
            last_failure = stats.get('last_failure')
            if last_failure and (datetime.now() - last_failure).seconds < self.failure_timeout:
                return False
            else:
                stats['failures'] = 0
        
        return True
    
    def get_proxy(self) -> Optional[str]:
        with self.lock:
            available_proxies = [p for p in self.proxies if self._is_proxy_available(p)]
            
            if not available_proxies:
                logger.warning('无可用的代理IP')
                return None
            
            proxy = available_proxies[self.current_index % len(available_proxies)]
            self.current_index += 1
            return proxy
    
    def mark_proxy_failed(self, proxy: str, reason: str = None):
        if proxy in self.proxy_stats:
            stats = self.proxy_stats[proxy]
            stats['failures'] += 1
            stats['last_failure'] = datetime.now()
            
            if stats['failures'] >= self.max_failures:
                stats['is_banned'] = True
                stats['ban_time'] = datetime.now()
                logger.warning(f'代理IP {proxy} 被标记为封禁，原因: {reason}')
            else:
                logger.warning(f'代理IP {proxy} 失败，当前失败次数: {stats["failures"]}')
    
    def mark_proxy_success(self, proxy: str):
        if proxy in self.proxy_stats:
            stats = self.proxy_stats[proxy]
            stats['successes'] += 1
            stats['last_success'] = datetime.now()
            stats['failures'] = 0
    
    def test_proxy(self, proxy: str) -> bool:
        try:
            proxy_dict = {
                'http': proxy,
                'https': proxy
            }
            response = requests.get(self.test_url, proxies=proxy_dict, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f'代理IP {proxy} 测试失败: {e}')
            return False
    
    def get_stats(self) -> Dict:
        return {
            'total_proxies': len(self.proxies),
            'available_proxies': len([p for p in self.proxies if self._is_proxy_available(p)]),
            'banned_proxies': len([p for p in self.proxies if self.proxy_stats[p].get('is_banned', False)]),
            'proxy_details': {
                proxy: {
                    'failures': stats['failures'],
                    'successes': stats['successes'],
                    'is_banned': stats['is_banned'],
                    'last_failure': stats['last_failure'].isoformat() if stats['last_failure'] else None,
                    'last_success': stats['last_success'].isoformat() if stats['last_success'] else None
                }
                for proxy, stats in self.proxy_stats.items()
            }
        }

class IPPoolManager:
    def __init__(self):
        self.proxy_pools: Dict[str, ProxyPool] = {}
        self.default_pool = None
    
    def create_pool(self, name: str, proxies: List[str] = None, **kwargs) -> ProxyPool:
        pool = ProxyPool(proxies, **kwargs)
        self.proxy_pools[name] = pool
        
        if not self.default_pool:
            self.default_pool = pool
        
        return pool
    
    def get_pool(self, name: str = None) -> Optional[ProxyPool]:
        if name:
            return self.proxy_pools.get(name)
        return self.default_pool
    
    def get_proxy(self, pool_name: str = None) -> Optional[str]:
        pool = self.get_pool(pool_name)
        return pool.get_proxy() if pool else None
    
    def mark_proxy_failed(self, proxy: str, pool_name: str = None, reason: str = None):
        pool = self.get_pool(pool_name)
        if pool:
            pool.mark_proxy_failed(proxy, reason)
    
    def mark_proxy_success(self, proxy: str, pool_name: str = None):
        pool = self.get_pool(pool_name)
        if pool:
            pool.mark_proxy_success(proxy)
    
    def get_stats(self) -> Dict:
        return {
            name: pool.get_stats()
            for name, pool in self.proxy_pools.items()
        }

# 全局IP池管理器
ip_pool_manager = IPPoolManager()

def init_proxy_pools(config: Dict):
    proxy_config = config.get('proxy_pools', {})
    
    for pool_name, pool_config in proxy_config.items():
        proxies = pool_config.get('proxies', [])
        max_failures = pool_config.get('max_failures', 3)
        failure_timeout = pool_config.get('failure_timeout', 3600)
        test_url = pool_config.get('test_url', 'https://httpbin.org/ip')
        
        ip_pool_manager.create_pool(
            name=pool_name,
            proxies=proxies,
            max_failures=max_failures,
            failure_timeout=failure_timeout,
            test_url=test_url
        )
    
    # 如果没有配置，创建默认的空池
    if not ip_pool_manager.proxy_pools:
        ip_pool_manager.create_pool('default', [])

def get_proxy_session(pool_name: str = None, user_agent: str = None) -> requests.Session:
    session = requests.Session()
    
    # 设置默认的请求头
    default_headers = {
        'User-Agent': user_agent or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0'
    }
    
    session.headers.update(default_headers)
    
    # 获取代理IP
    proxy = ip_pool_manager.get_proxy(pool_name)
    if proxy:
        proxies = {
            'http': proxy,
            'https': proxy
        }
        session.proxies.update(proxies)
        logger.info(f'使用代理IP: {proxy}')
    else:
        logger.info('未使用代理IP，使用本地网络')
    
    return session

def safe_request(url: str, method: str = 'GET', pool_name: str = None, 
                max_retries: int = 3, retry_delay: float = 1.0, 
                user_agent: str = None, **kwargs) -> requests.Response:
    
    for attempt in range(max_retries):
        try:
            session = get_proxy_session(pool_name, user_agent)
            proxy = session.proxies.get('http') or session.proxies.get('https')
            
            logger.info(f'请求URL: {url} (尝试 {attempt + 1}/{max_retries})')
            
            response = session.request(method, url, timeout=30, **kwargs)
            
            if response.status_code == 200:
                if proxy:
                    ip_pool_manager.mark_proxy_success(proxy)
                logger.info(f'请求成功: {url}')
                return response
            elif response.status_code in [403, 429, 503]:
                # 可能是被封禁或请求过多
                if proxy:
                    ip_pool_manager.mark_proxy_failed(proxy, f'HTTP {response.status_code}')
                logger.warning(f'请求可能被限制: {url}, 状态码: {response.status_code}')
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                    continue
            else:
                logger.warning(f'请求失败: {url}, 状态码: {response.status_code}')
                
        except requests.exceptions.ProxyError as e:
            if proxy:
                ip_pool_manager.mark_proxy_failed(proxy, f'代理错误: {str(e)}')
            logger.error(f'代理错误: {e}')
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (attempt + 1))
                continue
                
        except requests.exceptions.RequestException as e:
            if proxy:
                ip_pool_manager.mark_proxy_failed(proxy, f'请求错误: {str(e)}')
            logger.error(f'请求错误: {e}')
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (attempt + 1))
                continue
        
        except Exception as e:
            if proxy:
                ip_pool_manager.mark_proxy_failed(proxy, f'未知错误: {str(e)}')
            logger.error(f'未知错误: {e}')
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (attempt + 1))
                continue
    
    # 所有尝试都失败
    raise requests.exceptions.RequestException(f'请求失败，重试{max_retries}次后仍失败: {url}')
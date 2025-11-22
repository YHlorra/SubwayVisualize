import os
import sys
import logging
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from subway_visualize.services.proxy_pool import ip_pool_manager, safe_request
from subway_visualize.config import get_proxy_pools_config

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_proxy_pools():
    print('开始测试IP池功能...')
    
    # 初始化IP池
    proxy_config = get_proxy_pools_config()
    if not proxy_config:
        print('未配置代理IP池，使用本地网络进行测试')
        # 测试本地网络请求
        try:
            response = safe_request('https://httpbin.org/ip', max_retries=1)
            print(f'本地网络测试成功: {response.json()}')
            return True
        except Exception as e:
            print(f'本地网络测试失败: {e}')
            return False
    
    print(f'已配置的IP池: {list(proxy_config.keys())}')
    
    # 测试每个IP池
    for pool_name in proxy_config.keys():
        print(f'\n测试IP池: {pool_name}')
        pool = ip_pool_manager.get_pool(pool_name)
        
        if not pool:
            print(f'  IP池 {pool_name} 不存在')
            continue
        
        stats = pool.get_stats()
        print(f'  总代理数: {stats["total_proxies"]}')
        print(f'  可用代理数: {stats["available_proxies"]}')
        print(f'  被封禁代理数: {stats["banned_proxies"]}')
        
        # 测试HTTP请求
        test_urls = [
            'https://httpbin.org/ip',
            'https://httpbin.org/user-agent',
            'https://httpbin.org/headers'
        ]
        
        success_count = 0
        for i, test_url in enumerate(test_urls):
            try:
                print(f'  测试请求 {i+1}/{len(test_urls)}: {test_url}')
                response = safe_request(test_url, pool_name=pool_name, max_retries=2)
                if response.status_code == 200:
                    success_count += 1
                    print(f'    成功: HTTP {response.status_code}')
                else:
                    print(f'    失败: HTTP {response.status_code}')
            except Exception as e:
                print(f'    失败: {str(e)[:100]}...')
        
        print(f'  测试结果: {success_count}/{len(test_urls)} 成功')
        
        # 显示详细统计
        updated_stats = pool.get_stats()
        print(f'  测试后统计:')
        for proxy, details in updated_stats['proxy_details'].items():
            status = '可用' if not details['is_banned'] else '被封禁'
            print(f'    {proxy}: {status} (失败: {details["failures"]}, 成功: {details["successes"]})')
    
    # 显示总体统计
    print(f'\n总体统计:')
    overall_stats = ip_pool_manager.get_stats()
    for pool_name, stats in overall_stats.items():
        print(f'  {pool_name}: {stats["available_proxies"]}/{stats["total_proxies"]} 可用')
    
    return True

def test_specific_sites():
    print('\n测试特定网站访问...')
    
    # 测试高德地铁API
    try:
        print('测试高德地铁API...')
        response = safe_request(
            'https://map.amap.com/service/subway?_1707184339116&srhdata=citylist.json',
            pool_name='subway',
            max_retries=2
        )
        if response.status_code == 200:
            data = response.json()
            city_count = len(data.get('citylist', []))
            print(f'  成功获取城市列表: {city_count} 个城市')
        else:
            print(f'  失败: HTTP {response.status_code}')
    except Exception as e:
        print(f'  失败: {str(e)[:100]}...')
    
    # 测试安居客（使用本地网络，因为可能不需要代理）
    try:
        print('测试安居客网站...')
        response = safe_request(
            'https://bj.zu.anjuke.com/ditie/',
            pool_name='anjuke',
            max_retries=2
        )
        if response.status_code == 200:
            print(f'  成功访问安居客: HTTP {response.status_code}')
        else:
            print(f'  失败: HTTP {response.status_code}')
    except Exception as e:
        print(f'  失败: {str(e)[:100]}...')

if __name__ == '__main__':
    print('=== IP池功能测试 ===')
    
    # 基础测试
    test_proxy_pools()
    
    # 特定网站测试
    test_specific_sites()
    
    print('\n测试完成！')
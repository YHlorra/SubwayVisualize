from .app import app
from .config import get_proxy_pools_config
from .services.proxy_pool import init_proxy_pools

if __name__ == "__main__":
    # 初始化IP池
    proxy_config = get_proxy_pools_config()
    if proxy_config:
        init_proxy_pools({'proxy_pools': proxy_config})
        print(f'IP池已初始化，配置: {list(proxy_config.keys())}')
    else:
        print('未配置代理IP池')
    
    from waitress import serve
    serve(app, host="0.0.0.0", port=5000)

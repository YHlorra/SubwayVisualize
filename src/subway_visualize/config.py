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

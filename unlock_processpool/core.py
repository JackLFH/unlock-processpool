# unlock_processpool_workers.py
"""
Windows进程限制统一解锁器(兼容joblib和ProcessPoolExecutor)
版本：2.1.0
"""
import sys

# 核心配置
_UNLOCKED_MAX_WORKERS = 510  # 总句柄数限制
_SAVED_WAIT_API = None

if sys.platform == "win32":
    from typing import Sequence
    import _winapi

    def _hacked_wait(
        handles: Sequence[int],
        wait_all: bool,
        timeout: int = _winapi.INFINITE
    ) -> int:
        chunk_size = 63
        for idx in range(0, len(handles), chunk_size):
            chunk = handles[idx:idx+chunk_size]
            ret = _SAVED_WAIT_API(chunk, wait_all, timeout if idx == 0 else 0)
            if not wait_all and ret < 0x80:  # WAIT_OBJECT_0到WAIT_OBJECT_63
                return idx + ret
        return _winapi.WAIT_TIMEOUT

def please():
    """一键解锁"""
    if sys.platform != "win32":
        return False

    global _SAVED_WAIT_API
    if _SAVED_WAIT_API is None:
        _SAVED_WAIT_API = _winapi.WaitForMultipleObjects
        _winapi.WaitForMultipleObjects = _hacked_wait

    # 动态修改所有已知限制模块
    modules = [
        ("concurrent.futures.process", "_MAX_WINDOWS_WORKERS"),
        ("joblib.externals.loky.backend.context", "_MAX_WINDOWS_WORKERS"),
        ("joblib.externals.loky.process_executor", "_MAX_WINDOWS_WORKERS"),
        ("loky.backend.context", "_MAX_WINDOWS_WORKERS"),
    ]

    for mod, attr in modules:
        try:
            __import__(mod)
            module = sys.modules[mod]
            if hasattr(module, attr):
                setattr(module, attr, _UNLOCKED_MAX_WORKERS - 2)
        except:
            continue

    # 强制刷新joblib配置
    try:
        from joblib import parallel_backend
        parallel_backend("loky")
    except:
        pass

    return True
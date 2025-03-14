"""
核心补丁实现模块
"""
import sys

# 保存原始API引用
_Saved_WaitForMultipleObjects = None
_UNLOCKED_MAX_WINDOWS_WORKERS = 510  # 允许的最大句柄数

if sys.platform == "win32":
    # Windows专用实现
    from typing import Sequence
    import _winapi

    def _hacked_wait_for_multiple_objects(
        handle_seq: Sequence[int], 
        wait_all: bool, 
        timeout: int
    ) -> int:
        MAX_WAIT_OBJECTS = 63  # Windows API限制的每批最大句柄数

        if len(handle_seq) <= MAX_WAIT_OBJECTS:
            return _Saved_WaitForMultipleObjects(handle_seq, wait_all, timeout)

        results = []
        for i in range(0, len(handle_seq), MAX_WAIT_OBJECTS):
            chunk = handle_seq[i:i+MAX_WAIT_OBJECTS]
            chunk_timeout = timeout if i == 0 else 0
            ret = _Saved_WaitForMultipleObjects(chunk, wait_all, chunk_timeout)
            
            # 非等待全部模式直接返回
            if not wait_all and ret >= _winapi.WAIT_OBJECT_0:
                return i + (ret - _winapi.WAIT_OBJECT_0)
            results.append(ret)

        # 处理等待全部的结果
        if wait_all:
            if all(r == _winapi.WAIT_OBJECT_0 for r in results):
                return _winapi.WAIT_OBJECT_0
            return _winapi.WAIT_TIMEOUT if any(r == _winapi.WAIT_TIMEOUT for r in results) else _winapi.WAIT_FAILED
        return _winapi.WAIT_TIMEOUT

def please() -> bool:
    """应用补丁的主入口函数"""
    if sys.platform != "win32":
        return False

    global _Saved_WaitForMultipleObjects
    
    # 只执行一次Hook
    if _Saved_WaitForMultipleObjects is None:
        _Saved_WaitForMultipleObjects = _winapi.WaitForMultipleObjects
        _winapi.WaitForMultipleObjects = _hacked_wait_for_multiple_objects

    # 修改ProcessPoolExecutor内部限制
    try:
        import concurrent.futures.process as process
        if hasattr(process, '_MAX_WINDOWS_WORKERS'):
            process._MAX_WINDOWS_WORKERS = _UNLOCKED_MAX_WINDOWS_WORKERS - 2
    except ImportError:
        pass

    return True
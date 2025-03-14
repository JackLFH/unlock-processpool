import sys
import unittest
from unittest.mock import patch
import _winapi
import concurrent.futures.process as process
from unlock_processpool import please

class TestUnlock(unittest.TestCase):
    
    def test_patch_application(self):
        # 测试前状态
        original_wait = _winapi.WaitForMultipleObjects
        
        # 应用补丁
        result = please()
        self.assertTrue(result)
        
        # 验证API是否被Hook
        self.assertNotEqual(_winapi.WaitForMultipleObjects, original_wait)
        
        # 验证进程数限制
        if sys.platform == "win32":
            self.assertEqual(process._MAX_WINDOWS_WORKERS, 508)  # 510 - 2

    @unittest.skipIf(sys.platform != "win32", "仅Windows测试")
    def test_worker_limit(self):
        # 测试是否能突破默认限制
        please()
        
        try:
            with concurrent.futures.ProcessPoolExecutor(max_workers=100) as executor:
                results = list(executor.map(lambda x: x*2, range(50)))
                self.assertEqual(len(results), 50)
        except Exception as e:
            self.fail(f"创建进程池失败: {str(e)}")

    def test_non_windows_behavior(self):
        # 模拟非Windows环境
        with patch('sys.platform', 'linux'):
            result = please()
            self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
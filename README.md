# unlock-processpool-win
解锁 Windows 下 ProcessPoolExecutor 最大进程数限制的 Python 工具包 / Unlock ProcessPoolExecutor's worker limit on Windows

[![PyPI version](https://img.shields.io/pypi/v/unlock-processpool-win)](https://pypi.org/project/unlock-processpool-win/)
[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)

## 功能特性
- 解除 Windows 平台默认 61 进程限制
- 支持 Python 3.8-3.12
- 无需修改系统配置

## 安装方法
```bash
pip install unlock-processpool-win
```

## 使用方法
```python
import unlock_processpool
unlock_processpool.please()  # 必须在创建Executor前调用

from concurrent.futures import ProcessPoolExecutor
with ProcessPoolExecutor(max_workers=100) as executor:
    # 您的并发代码
```

## 许可证
BSD 3-Clause License [查看完整协议](LICENSE)
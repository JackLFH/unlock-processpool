# 逻辑契约文档（Logic Contracts）

## 📋 什么是逻辑契约？

逻辑契约是一种形式化的规约方法，用于确保代码修改不会破坏原有的正确行为。

**核心要素**:
- **Pre-conditions（前置条件）**: 函数执行前必须满足的条件
- **Post-conditions（后置条件）**: 函数执行后保证的结果
- **Invariants（不变量）**: 函数执行过程中不变的全局状态
- **Side effects（副作用）**: 函数可能产生的副作用

---

## 📝 契约模板

```python
def function_name(param1, param2):
    """
    简短功能描述

    Pre-conditions（前置条件）:
      - param1必须满足条件A
      - param2必须在范围[min, max]内
      - 全局状态B已初始化

    Post-conditions（后置条件）:
      - 返回值满足条件C
      - 不修改输入参数
      - 全局状态D被正确更新

    Invariants（不变量）:
      - 全局配置E保持不变
      - 文件系统不被修改

    Side effects（副作用）:
      - 可能调用外部API
      - 可能写日志文件
      - 不修改数据库

    Raises:
      - TypeError: 如果param1类型错误
      - ValueError: 如果param2超出范围

    Examples:
      >>> function_name(valid_param1, valid_param2)
      expected_result
    """
    # 实现
```

---

## 🎯 核心函数的逻辑契约

### 1. `_hacked_wait(handles, wait_all, timeout)`

```python
"""
绕过Windows WaitForMultipleObjects的64句柄限制

Pre-conditions（前置条件）:
  1. handles 是 list 或 tuple 类型
  2. handles 中的所有元素都是整数（Windows句柄）
  3. 0 <= len(handles) <= 508
  4. wait_all 是 bool 类型
  5. timeout >= -1 或 timeout == _winapi.INFINITE
  6. _SAVED_WAIT_API is not None（已初始化）

Post-conditions（后置条件）:
  当 wait_all=False 时:
    - 如果任意句柄就绪，返回就绪句柄的全局索引 [0, len(handles))
    - 如果任意句柄abandoned，返回 WAIT_ABANDONED_0 + 全局索引
    - 如果全部超时，返回 WAIT_TIMEOUT (0x102)
    - 如果失败，返回 WAIT_FAILED (0xFFFFFFFF)

  当 wait_all=True 时:
    - 如果所有句柄都就绪，返回 WAIT_OBJECT_0 (0x00)
    - 如果任意句柄abandoned，返回 WAIT_ABANDONED_0 + 全局索引
    - 如果超时，返回 WAIT_TIMEOUT (0x102)
    - 如果失败，返回 WAIT_FAILED (0xFFFFFFFF)

Invariants（不变量）:
  - handles 的内容不被修改（只读）
  - _SAVED_WAIT_API 不被修改
  - _PLEASE_LOCK 状态不变
  - 全局配置 _UNLOCKED_MAX_WORKERS 不变

Side effects（副作用）:
  - 调用 _SAVED_WAIT_API（原始Windows API）
  - 可能写debug日志（通过_logger）
  - 不修改文件系统
  - 不修改进程状态

Raises:
  - RuntimeError: 如果_SAVED_WAIT_API未初始化（未调用please()）
  - TypeError: 如果handles类型错误或包含非整数元素
  - ValueError: 如果len(handles) > 508

Performance:
  - 时间复杂度: O(n/63) 其中n是句柄数量
  - 空间复杂度: O(1) （不额外分配内存）
  - 额外开销: <5% 相比原生API

Thread Safety:
  - 线程安全（可以在多线程中调用）
  - 不需要外部同步

Examples:
  >>> handles = [event1, event2, event3]
  >>> result = _hacked_wait(handles, wait_all=False, timeout=1000)
  >>> assert 0 <= result < 3 or result in [WAIT_TIMEOUT, WAIT_FAILED]
"""
```

#### 关键测试用例（验证契约）

```python
def test_contract_wait_any_basic():
    """验证wait_all=False的基本契约"""
    # Pre-condition: 有效输入
    handles = [0, 1, 2]  # Mock handles

    # 执行
    result = _hacked_wait(handles, wait_all=False, timeout=1000)

    # Post-condition: 返回值在预期范围
    assert 0 <= result < len(handles) or \
           result in [WAIT_TIMEOUT, WAIT_FAILED, WAIT_ABANDONED_0 + 0, ...]

def test_contract_invariants():
    """验证不变量"""
    handles_before = [0, 1, 2]
    handles = handles_before.copy()
    saved_api_before = _SAVED_WAIT_API

    # 执行
    _hacked_wait(handles, wait_all=False, timeout=1000)

    # Invariant: handles内容不变
    assert handles == handles_before

    # Invariant: _SAVED_WAIT_API不变
    assert _SAVED_WAIT_API is saved_api_before
```

---

### 2. `please()`

```python
"""
一键解锁Windows进程池限制（幂等操作）

Pre-conditions（前置条件）:
  - 无（可以在任何时候调用）
  - 可以被多次调用（幂等）

Post-conditions（后置条件）:
  在Windows平台 (sys.platform == "win32"):
    - _winapi.WaitForMultipleObjects 被替换为 _hacked_wait
    - _SAVED_WAIT_API 保存了原始的 WaitForMultipleObjects
    - 返回 True
    - 可以创建 >61 workers 的进程池

  在非Windows平台:
    - 不做任何修改
    - 返回 False

Invariants（不变量）:
  - 多次调用是幂等的（第二次调用不改变任何状态）
  - 线程安全（使用_PLEASE_LOCK保护）
  - 第一次调用后，_SAVED_WAIT_API 永远不会再变

Side effects（副作用）:
  - 修改全局变量 _SAVED_WAIT_API
  - 修改全局变量 _winapi.WaitForMultipleObjects（仅Windows）
  - 修改 sys.modules 中已导入模块的 _MAX_WINDOWS_WORKERS 属性
    - concurrent.futures.process
    - joblib.externals.loky.backend.context
    - joblib.externals.loky.process_executor
    - loky.backend.context
  - 可能调用 joblib.parallel_backend()
  - 写debug日志

Raises:
  - 无异常（所有错误都被捕获并忽略）

Thread Safety:
  - 线程安全（使用RLock保护临界区）
  - 多线程同时调用会被串行化

Idempotency（幂等性）:
  - 可以安全地多次调用
  - 第二次及后续调用会立即返回（检测到已初始化）

Examples:
  >>> import unlock_processpool
  >>> success = unlock_processpool.please()
  >>> assert success == (sys.platform == "win32")
  >>>
  >>> # 第二次调用（幂等）
  >>> success2 = unlock_processpool.please()
  >>> assert success2 == success
"""
```

#### 关键测试用例

```python
def test_contract_please_idempotency():
    """验证幂等性契约"""
    # 第一次调用
    result1 = please()
    saved_api_1 = _SAVED_WAIT_API
    current_api_1 = _winapi.WaitForMultipleObjects

    # 第二次调用（幂等）
    result2 = please()
    saved_api_2 = _SAVED_WAIT_API
    current_api_2 = _winapi.WaitForMultipleObjects

    # Post-condition: 结果相同
    assert result1 == result2

    # Invariant: _SAVED_WAIT_API不变
    assert saved_api_1 is saved_api_2

    # Invariant: _winapi.WaitForMultipleObjects不变
    assert current_api_1 is current_api_2

def test_contract_please_thread_safety():
    """验证线程安全契约"""
    import threading
    results = []

    def call_please():
        results.append(please())

    # 20个线程同时调用
    threads = [threading.Thread(target=call_please) for _ in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Post-condition: 所有结果相同
    assert all(r == results[0] for r in results)

    # Invariant: _SAVED_WAIT_API一致
    # （不会有部分线程看到不同的值）
```

---

## 🔍 如何使用逻辑契约

### 修改代码前

1. **阅读现有契约**
   - 理解函数的前置条件、后置条件、不变量
   - 识别哪些行为必须保持不变

2. **编写黄金测试**
   - 为所有契约编写测试用例
   - 运行测试，确保当前代码满足契约

3. **声明修改意图**
   ```python
   """
   修改目标: 添加输入验证

   契约变更:
     - Pre-conditions: 新增handles类型检查
     - Post-conditions: 新增TypeError异常
     - Invariants: 不变（所有正确输入的行为不变）
   """
   ```

### 修改代码中

4. **更新契约文档**
   - 如果修改了行为，更新契约
   - 如果只是重构，契约不变

5. **编写验证测试**
   - 为新的契约编写测试
   - 确保所有契约都有对应测试

### 修改代码后

6. **验证契约**
   ```bash
   # 运行契约测试
   pytest tests/unit/test_contracts.py -v

   # 运行黄金测试
   pytest tests/golden/ -v
   ```

7. **性能契约验证**
   ```bash
   # 运行性能测试
   pytest tests/benchmarks/ --benchmark-only

   # 对比基线
   python scripts/compare_performance.py
   ```

---

## 📋 契约检查清单

### 每次修改前
- [ ] 已阅读相关函数的逻辑契约
- [ ] 已理解不变量
- [ ] 已编写黄金测试

### 每次修改后
- [ ] 契约文档已更新（如果有变更）
- [ ] 所有契约测试通过
- [ ] 黄金测试100%通过
- [ ] 性能契约满足（无回归）

---

## 🎓 契约示例：添加输入验证

### 修改前的契约

```python
"""
Pre-conditions:
  - handles可以是任何对象（无验证）

Post-conditions:
  - 如果handles为空列表，返回WAIT_FAILED
  - 否则，继续处理
"""
```

### 修改后的契约

```python
"""
Pre-conditions:
  - handles 必须是 list 或 tuple
  - handles 中所有元素必须是 int
  - len(handles) <= 508

Post-conditions:
  - 如果违反前置条件，抛出 TypeError 或 ValueError
  - 如果handles为空列表，返回WAIT_FAILED
  - 否则，行为与修改前完全相同

Invariants:
  - 所有满足新前置条件的输入，行为不变
"""
```

### 验证测试

```python
def test_contract_input_validation():
    """验证新契约：输入验证"""
    # 违反前置条件 → 应该抛出异常
    with pytest.raises(TypeError):
        _hacked_wait("invalid", False, 1000)

    with pytest.raises(ValueError):
        _hacked_wait(list(range(509)), False, 1000)

    # 满足前置条件 → 行为不变
    # 与黄金测试对比，确保逻辑等价
```

---

**文档版本**: 1.0
**最后更新**: 2025-10-21
**适用项目**: unlock-processpool v2.2.0+

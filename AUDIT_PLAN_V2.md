# unlock-processpool 全面审核方案 v2.0
## 防御性·可验证·避免修复死循环

**制定日期**: 2025-10-21
**预计完成**: 2025-11-07 (17天)
**当前状态**: ✅ 方案已批准，准备开始执行

---

## 📋 执行概览

### 核心目标
1. ✅ 发现并修复所有潜在bug
2. ✅ 提升代码可维护性至行业优秀水平
3. ✅ 建立防御性验证机制（避免修复死循环）
4. ✅ 建立持续审核流程

### 关键成果
- **代码质量**: 6.8/10 → 9.0/10 (+32%)
- **测试覆盖**: 97% → 99%+
- **圈复杂度**: 20 → <7
- **已知BUG**: 5个 → 0个

---

## 🛡️ 四大防护机制（避免修复死循环）

### 1. 逻辑契约（Logic Contracts）
每个修改都必须声明：
- **Pre-conditions（前置条件）**: 修改前必须满足的条件
- **Post-conditions（后置条件）**: 修改后保证的结果
- **Invariants（不变量）**: 修改过程中不变的全局状态

### 2. 黄金测试套件（Golden Tests）
修改前锁定所有正确行为：
```python
# 修改前运行
pytest tests/golden/ > golden_baseline.txt

# 修改后对比
pytest tests/golden/ > golden_after.txt
diff golden_baseline.txt golden_after.txt  # 必须为空
```

### 3. 增量验证（Incremental Verification）
每次commit都运行完整测试：
```bash
git commit -m "..."
pytest tests/ --cov  # 自动运行
```

### 4. 回滚点（Rollback Points）
每个阶段都可以安全回退：
```bash
# 保存回滚点
git tag audit/phase-1-complete

# 如果失败，回滚
git reset --hard audit/phase-1-complete
```

---

## 📅 详细执行计划

### 阶段0: 准备阶段（第1天）

#### 目标
建立审核基础设施和保护机制

#### 任务清单

| 任务 | 工作量 | 负责人 | 状态 |
|------|--------|--------|------|
| 创建Git审核分支 | 5分钟 | DEV | ⏳ 待开始 |
| 建立性能基线 | 30分钟 | DEV | ⏳ 待开始 |
| 创建黄金测试套件 | 2小时 | DEV | ⏳ 待开始 |
| 安装审核工具 | 30分钟 | DEV | ⏳ 待开始 |
| 编写逻辑契约 | 2小时 | DEV | ⏳ 待开始 |

#### 验收标准
- [ ] Git分支 `audit/v2-comprehensive` 创建成功
- [ ] 性能基线文件 `baseline.json` 存在
- [ ] 黄金测试套件 `tests/golden/` 创建并通过
- [ ] 工具安装成功：pylint, mypy, radon, pytest-cov
- [ ] 逻辑契约文档 `LOGIC_CONTRACTS.md` 创建

#### 命令清单
```bash
# 1. 创建审核分支
git checkout -b audit/v2-comprehensive
git push -u origin audit/v2-comprehensive

# 2. 安装审核工具
pip install pylint mypy radon pytest-cov pytest-benchmark bandit

# 3. 运行性能基线测试
python test_auto.py
# 手动保存输出到baseline.json

# 4. 创建黄金测试
pytest tests/ -v > tests/golden/baseline_results.txt

# 5. 标记回滚点
git tag audit/phase-0-complete
```

---

### 阶段1: 关键BUG修复（第2-4天）

#### 任务1.1: 添加输入验证（独立任务）

**文件**: `unlock_processpool/core.py:31-35`

**逻辑契约**:
```python
"""
Pre-conditions:
  - 无（可以接受任何输入）

Post-conditions:
  - 如果handles不是list/tuple，抛出TypeError
  - 如果handles包含非int元素，抛出TypeError
  - 如果len(handles) > 508，抛出ValueError
  - 否则，继续原有逻辑

Invariants:
  - 不影响现有正确输入的处理
  - 所有合法输入的行为不变
"""
```

**修改内容**:
```python
def _hacked_wait(handles, wait_all, timeout):
    """..."""
    # ✅ 新增输入验证
    if not isinstance(handles, (list, tuple)):
        raise TypeError(
            f"handles必须是list或tuple类型，实际为{type(handles).__name__}"
        )

    if any(not isinstance(h, int) for h in handles):
        raise TypeError("handles必须包含整数句柄")

    if len(handles) > 508:
        raise ValueError(
            f"句柄数量超过上限：{len(handles)} > 508。"
            f"建议使用多个进程池或减少并发数量。"
        )

    # 原有的空列表检查
    if not handles:
        _logger.debug("空句柄列表，返回WAIT_FAILED")
        return WAIT_FAILED

    # ... 原有代码继续
```

**测试用例**:
```python
# tests/unit/test_input_validation.py
def test_handles_type_validation():
    """测试handles类型验证"""
    with pytest.raises(TypeError, match="必须是list或tuple"):
        _hacked_wait("invalid", False, 1000)

    with pytest.raises(TypeError, match="必须是list或tuple"):
        _hacked_wait(12345, False, 1000)

def test_handles_content_validation():
    """测试handles内容验证"""
    with pytest.raises(TypeError, match="必须包含整数句柄"):
        _hacked_wait(["string", "handle"], False, 1000)

def test_handles_count_validation():
    """测试handles数量验证"""
    with pytest.raises(ValueError, match="超过上限"):
        _hacked_wait(list(range(509)), False, 1000)
```

**验证步骤**:
1. 编写测试用例：`tests/unit/test_input_validation.py`
2. 运行测试，确认失败（因为代码未修改）
3. 修改代码
4. 运行测试，确认通过
5. 运行全部测试，确认无回归
6. 运行黄金测试，确认100%通过
7. Commit: `feat: 添加输入验证（BUG#4修复）`

**回滚命令**:
```bash
# 如果失败
git reset --hard HEAD^
```

---

#### 任务1.2: 验证BUG#1是否已修复

**文件**: `unlock_processpool/core.py:137-139`

**当前代码**:
```python
elif WAIT_ABANDONED_0 <= ret < WAIT_ABANDONED_0 + 64:
    # ✅ P0修复#1（BUG #1）: 调整abandoned索引到全局范围（和wait_all=False保持一致）
    return WAIT_ABANDONED_0 + idx + (ret - WAIT_ABANDONED_0)
```

**验证命令**:
```bash
# 运行BUG#1的测试
pytest tests/test_deep_audit.py::TestDeepAudit::test_wait_all_abandoned_index_adjustment -v

# 如果通过 → BUG#1已修复 ✅
# 如果失败 → 需要检查代码
```

**逻辑契约验证**:
```python
"""
Pre-conditions:
  - ret in [WAIT_ABANDONED_0, WAIT_ABANDONED_0+63]
  - idx是当前批次的起始索引
  - wait_all=True

Post-conditions:
  - 返回全局索引 WAIT_ABANDONED_0 + idx + (ret - WAIT_ABANDONED_0)
  - 例如：第70个句柄abandoned（idx=63, ret=0x87）
    → 应返回 0x80 + 63 + 7 = 0xCA
  - 而不是直接返回 0x87

Invariants:
  - wait_all=False的逻辑保持不变
  - 单批次的处理不受影响
"""
```

**如果测试失败，修复步骤**:
1. 检查代码是否与逻辑契约一致
2. 如果不一致，修改代码
3. 重新运行测试
4. Commit: `fix: 验证并确认BUG#1已修复`

---

#### 任务1.3: 并发安全加固

**问题**: `core.py:98, 127` - _SAVED_WAIT_API读取无锁保护（理论风险）

**修改方案**: 提前检查，减少重复代码
```python
def _hacked_wait(handles, wait_all, timeout):
    """..."""
    # 输入验证...

    # ✅ 提前检查_SAVED_WAIT_API，只检查一次
    saved_api = _SAVED_WAIT_API
    if saved_api is None:
        raise RuntimeError(
            "unlock_processpool未初始化。"
            "请在创建ProcessPoolExecutor前调用 unlock_processpool.please()"
        )

    # 后续逻辑都使用局部变量 saved_api
    # 不再重复检查
```

**逻辑契约**:
```python
"""
Pre-conditions:
  - _SAVED_WAIT_API可能为None或有效函数

Post-conditions:
  - 如果为None，抛出清晰的异常
  - 如果有效，保存到局部变量
  - 后续逻辑使用局部变量，不受并发影响

Invariants:
  - 性能损失 <1%（因为减少了重复检查）
  - 逻辑行为不变
"""
```

**验证步骤**:
1. 修改代码，删除两处重复检查
2. 运行多线程测试：`pytest tests/test_concurrency.py -v`
3. 运行性能测试，确认性能不下降
4. Commit: `refactor: 提前检查_SAVED_WAIT_API，提升并发安全性和性能`

---

#### 阶段1验收标准

- [ ] BUG#4（输入验证）修复完成，有3个负面测试
- [ ] BUG#1验证完成，测试通过
- [ ] 并发安全加固完成
- [ ] 所有现有测试通过（110/110）
- [ ] 黄金测试套件：100%通过
- [ ] 性能基线对比：下降 <2%
- [ ] Git标签：`audit/phase-1-complete`

---

### 阶段2: 测试体系完善（第5-9天）

#### 任务2.1: 重组测试目录

**目标结构**:
```
tests/
  unit/                       # 单元测试
    test_core_hacked_wait.py
    test_please.py
    test_input_validation.py  # 新增
  integration/                # 集成测试
    test_processpool.py
    test_joblib.py
  security/                   # 安全测试
    test_security_audit.py
  stress/                     # 压力测试
    ultimate_stress_test.py
  golden/                     # 黄金测试（新增）
    test_golden_behavior.py
    baseline_results.txt
  conftest.py
  helpers.py
```

**迁移脚本**:
```bash
# 创建新目录
mkdir -p tests/{unit,integration,security,stress,golden}

# 迁移现有测试
mv tests/test_core_hacked_wait.py tests/unit/
mv tests/test_integration_executor.py tests/integration/test_processpool.py
mv test_security_audit.py tests/security/
mv ultimate_stress_test.py tests/stress/

# 删除或移动根目录的测试脚本到scripts/
mkdir -p scripts/analysis
mv test_*.py scripts/analysis/  # 保留分析脚本
```

**验证**:
```bash
# pytest应该自动发现所有测试
pytest tests/ --collect-only

# 运行所有测试
pytest tests/ -v

# 检查覆盖率
pytest tests/ --cov=unlock_processpool
```

---

#### 任务2.2: 创建真实Windows句柄测试

**文件**: `tests/unit/test_real_handles.py`

**测试清单**:
```python
import _winapi
import pytest
from unlock_processpool import please

class TestRealWindowsHandles:
    """使用真实Windows句柄测试"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """初始化unlock_processpool"""
        please()

    def test_real_single_event(self):
        """测试1: 单个Event句柄"""
        event = _winapi.CreateEvent(None, False, False, None)
        try:
            _winapi.SetEvent(event)
            result = _winapi.WaitForMultipleObjects([event], False, 1000)
            assert result == 0, "单个event应该返回0"
        finally:
            _winapi.CloseHandle(event)

    def test_real_100_events(self):
        """测试2: 100个Event句柄（跨批次）"""
        events = []
        try:
            # 创建100个events
            for _ in range(100):
                event = _winapi.CreateEvent(None, False, False, None)
                events.append(event)

            # 全部设为signaled
            for e in events:
                _winapi.SetEvent(e)

            # 测试wait_all=True
            result = _winapi.WaitForMultipleObjects(events, True, 5000)
            assert result == 0, "所有event就绪应返回WAIT_OBJECT_0"

        finally:
            for e in events:
                _winapi.CloseHandle(e)

    def test_real_timeout_behavior(self):
        """测试3: 真实超时行为"""
        event = _winapi.CreateEvent(None, False, False, None)
        try:
            # 不设置event，应该超时
            import time
            start = time.time()
            result = _winapi.WaitForMultipleObjects([event], False, 100)
            duration = time.time() - start

            assert result == 0x00000102, "应该返回WAIT_TIMEOUT"
            assert 0.08 < duration < 0.15, f"超时时间应该约100ms，实际{duration*1000:.1f}ms"
        finally:
            _winapi.CloseHandle(event)

    def test_real_invalid_handle(self):
        """测试4: 无效句柄应该抛出异常"""
        invalid_handle = 0xDEADBEEF
        with pytest.raises(OSError):
            _winapi.WaitForMultipleObjects([invalid_handle], False, 0)

    def test_real_200_events_stress(self):
        """测试5: 200个Event压力测试"""
        events = []
        try:
            for _ in range(200):
                event = _winapi.CreateEvent(None, False, False, None)
                events.append(event)

            # 设置第150个event
            _winapi.SetEvent(events[150])

            # 测试wait_any
            result = _winapi.WaitForMultipleObjects(events, False, 5000)
            assert result == 150, f"应该返回150，实际{result}"

        finally:
            for e in events:
                _winapi.CloseHandle(e)
```

**验证**:
```bash
pytest tests/unit/test_real_handles.py -v
```

---

#### 任务2.3: 补充边界条件测试

**文件**: `tests/unit/test_edge_cases.py`

```python
def test_timeout_edge_wait_any():
    """补充覆盖: core.py:95 超时前检查"""
    # 测试在超时前0.001秒的行为
    ...

def test_timeout_edge_wait_all():
    """补充覆盖: core.py:123 超时前检查"""
    ...

def test_joblib_config_failure():
    """补充覆盖: core.py:214-216 joblib配置失败"""
    ...
```

---

#### 阶段2验收标准

- [ ] 测试目录重组完成
- [ ] pytest自动发现所有测试
- [ ] 5个真实Windows句柄测试通过
- [ ] 边界条件测试补充完成
- [ ] 代码覆盖率: 97% → 99%+
- [ ] 所有测试通过
- [ ] Git标签：`audit/phase-2-complete`

---

### 阶段3: 代码重构（第10-16天）

（详细内容见方案文档）

---

### 阶段4: CI/CD和自动化（第17天）

（详细内容见方案文档）

---

## 📝 日常检查清单

### 每次commit前
- [ ] 运行单元测试：`pytest tests/unit/ -v`
- [ ] 运行集成测试：`pytest tests/integration/ -v`
- [ ] 检查代码覆盖率：`pytest --cov`
- [ ] 运行黄金测试：`pytest tests/golden/ -v`
- [ ] 检查代码质量：`pylint unlock_processpool/`
- [ ] 检查类型提示：`mypy unlock_processpool/`

### 每次合并PR前
- [ ] 所有测试通过（110+个）
- [ ] 代码覆盖率 >99%
- [ ] pylint评分 >9.0
- [ ] mypy无错误
- [ ] 黄金测试100%通过
- [ ] 性能基线无回归

---

## 🚨 紧急回滚程序

### 如果某个阶段完全失败
```bash
# 1. 立即停止工作
git stash  # 保存当前更改

# 2. 回滚到上一个稳定点
git reset --hard audit/phase-N-complete  # N是上一个完成的阶段

# 3. 重新评估问题
# 4. 调整方案后重新开始
```

### 如果单个commit出问题
```bash
# 回滚单个commit
git revert HEAD
# 或
git reset --hard HEAD^
```

---

## 📊 进度跟踪

### 当前状态

| 阶段 | 状态 | 进度 | 预计完成 |
|------|------|------|---------|
| 阶段0: 准备 | ⏳ 待开始 | 0% | Day 1 |
| 阶段1: BUG修复 | ⏳ 待开始 | 0% | Day 2-4 |
| 阶段2: 测试完善 | ⏳ 待开始 | 0% | Day 5-9 |
| 阶段3: 代码重构 | ⏳ 待开始 | 0% | Day 10-16 |
| 阶段4: CI/CD | ⏳ 待开始 | 0% | Day 17 |

### 里程碑

- [ ] 2025-10-21: 方案批准 ✅
- [ ] 2025-10-22: 阶段0完成
- [ ] 2025-10-24: 阶段1完成（BUG清零）
- [ ] 2025-10-29: 阶段2完成（测试99%+）
- [ ] 2025-11-05: 阶段3完成（代码重构）
- [ ] 2025-11-07: 阶段4完成（CI/CD）

---

## 📧 联系方式

**项目负责人**: Half open flowers
**Email**: 1816524875@qq.com
**GitHub**: unlock-processpool

---

**文档版本**: 2.0
**最后更新**: 2025-10-21
**下次更新**: 每天更新进度

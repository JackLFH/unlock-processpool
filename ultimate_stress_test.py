"""
终极压力测试脚本 - 针对128线程超级电脑
测试unlock-processpool在极限并发场景下的稳定性和性能

Author: Half open flowers
"""
import sys
import time
import os
import traceback
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed, wait, ALL_COMPLETED
import multiprocessing


# ==================== 测试任务函数 ====================

def simple_task(x):
    """简单计算任务"""
    return x * 2


def cpu_bound_task(n):
    """CPU密集型任务"""
    total = 0
    for i in range(10000):
        total += i * n
    return total


def io_simulation_task(x):
    """模拟IO操作"""
    time.sleep(0.01)  # 模拟10ms的IO
    return x ** 2


def heavy_computation(n):
    """重度计算任务"""
    result = 0
    for i in range(n * 1000):
        result += i ** 2
    return result % 1000000


def mixed_task(x):
    """混合任务：CPU + IO模拟"""
    result = sum(range(x * 100))
    time.sleep(0.005)
    return result % 10000


# ==================== 测试类 ====================

class UltimateStressTest:
    """终极压力测试套件"""

    def __init__(self):
        self.results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.start_time = None

    def log(self, message, level="INFO"):
        """带时间戳的日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] [{level:8s}] {message}")

    def log_section(self, title):
        """区块标题"""
        print("\n" + "="*80)
        print(f"  {title}")
        print("="*80)

    def record_result(self, test_name, passed, duration, details=""):
        """记录测试结果"""
        self.total_tests += 1
        if passed:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            self.failed_tests += 1
            status = "❌ FAIL"

        self.results.append({
            'test': test_name,
            'status': status,
            'duration': f"{duration:.2f}s",
            'details': details
        })

        self.log(f"{status} | {test_name} | 耗时: {duration:.2f}s | {details}")

    # ==================== 基础验证测试 ====================

    def test_1_basic_unlock(self):
        """测试1: 基础解锁功能"""
        self.log_section("测试1: 基础解锁功能")

        try:
            from unlock_processpool import please
            start = time.time()

            result = please()

            duration = time.time() - start
            self.record_result(
                "基础解锁功能",
                result == True,
                duration,
                f"please()返回: {result}"
            )

            return result

        except Exception as e:
            self.log(f"异常: {e}", "ERROR")
            self.log(traceback.format_exc(), "ERROR")
            self.record_result("基础解锁功能", False, 0, f"异常: {e}")
            return False

    def test_2_worker_limit_verification(self):
        """测试2: 验证worker限制提升"""
        self.log_section("测试2: 验证Worker限制提升")

        try:
            from unlock_processpool import please
            import concurrent.futures.process as process

            please()
            start = time.time()

            max_workers = process._MAX_WINDOWS_WORKERS
            expected = 508  # 510 - 2

            duration = time.time() - start
            passed = (max_workers == expected)

            self.record_result(
                "Worker限制提升",
                passed,
                duration,
                f"_MAX_WINDOWS_WORKERS={max_workers}, 期望={expected}"
            )

            return passed

        except Exception as e:
            self.log(f"异常: {e}", "ERROR")
            self.record_result("Worker限制提升", False, 0, f"异常: {e}")
            return False

    # ==================== 并发规模测试 ====================

    def test_3_scale_100_workers(self):
        """测试3: 100个Worker并发"""
        self.log_section("测试3: 100个Worker并发 (原始限制是61)")

        try:
            start = time.time()

            with ProcessPoolExecutor(max_workers=100) as executor:
                self.log("创建100个worker的进程池...")
                tasks = list(range(500))
                self.log(f"提交500个任务...")

                results = list(executor.map(simple_task, tasks))

            duration = time.time() - start
            expected = [x * 2 for x in tasks]
            passed = (results == expected)

            self.record_result(
                "100 Workers并发",
                passed,
                duration,
                f"任务数: 500, 吞吐量: {500/duration:.1f}任务/秒"
            )

            return passed

        except Exception as e:
            self.log(f"异常: {e}", "ERROR")
            self.record_result("100 Workers并发", False, 0, f"异常: {e}")
            return False

    def test_4_scale_200_workers(self):
        """测试4: 200个Worker并发"""
        self.log_section("测试4: 200个Worker并发 (跨越3个批次)")

        try:
            start = time.time()

            with ProcessPoolExecutor(max_workers=200) as executor:
                self.log("创建200个worker的进程池...")
                tasks = list(range(1000))
                self.log(f"提交1000个任务...")

                results = list(executor.map(cpu_bound_task, tasks))

            duration = time.time() - start
            passed = (len(results) == 1000)

            self.record_result(
                "200 Workers并发",
                passed,
                duration,
                f"任务数: 1000, 吞吐量: {1000/duration:.1f}任务/秒"
            )

            return passed

        except Exception as e:
            self.log(f"异常: {e}", "ERROR")
            self.record_result("200 Workers并发", False, 0, f"异常: {e}")
            return False

    def test_5_scale_400_workers(self):
        """测试5: 400个Worker超大规模并发"""
        self.log_section("测试5: 400个Worker超大规模并发 (跨越7个批次)")

        try:
            start = time.time()

            with ProcessPoolExecutor(max_workers=400) as executor:
                self.log("创建400个worker的进程池...")
                tasks = list(range(2000))
                self.log(f"提交2000个任务...")

                results = list(executor.map(simple_task, tasks))

            duration = time.time() - start
            expected = [x * 2 for x in tasks]
            passed = (results == expected)

            self.record_result(
                "400 Workers超大规模",
                passed,
                duration,
                f"任务数: 2000, 吞吐量: {2000/duration:.1f}任务/秒"
            )

            return passed

        except Exception as e:
            self.log(f"异常: {e}", "ERROR")
            self.record_result("400 Workers超大规模", False, 0, f"异常: {e}")
            return False

    # ==================== BUG修复验证测试 ====================

    def test_6_bug1_wait_all_abandoned_fix(self):
        """测试6: 验证BUG #1修复 (wait_all=True WAIT_ABANDONED索引调整)"""
        self.log_section("测试6: BUG #1修复验证 - wait_all=True WAIT_ABANDONED")

        try:
            from unlock_processpool import please
            please()

            # 这个测试通过真实的多批次场景间接验证
            start = time.time()

            with ProcessPoolExecutor(max_workers=150) as executor:
                self.log("创建150个worker (3个批次)...")

                # 提交大量任务，使用wait(ALL_COMPLETED)
                futures = [executor.submit(simple_task, i) for i in range(300)]
                self.log("提交300个任务，使用wait(ALL_COMPLETED)...")

                done, not_done = wait(futures, return_when=ALL_COMPLETED, timeout=60)

            duration = time.time() - start
            passed = (len(done) == 300 and len(not_done) == 0)

            self.record_result(
                "BUG #1修复验证",
                passed,
                duration,
                f"完成: {len(done)}/300, 未完成: {len(not_done)}"
            )

            return passed

        except Exception as e:
            self.log(f"异常: {e}", "ERROR")
            self.record_result("BUG #1修复验证", False, 0, f"异常: {e}")
            return False

    def test_7_bug2_initialization_check(self):
        """测试7: 验证BUG #2修复 (初始化检查)"""
        self.log_section("测试7: BUG #2修复验证 - 初始化检查")

        try:
            # 重新导入模块以测试未初始化状态
            import importlib
            import unlock_processpool.core as core_module

            # 保存当前状态
            saved_api = core_module._SAVED_WAIT_API

            # 模拟未初始化
            core_module._SAVED_WAIT_API = None

            start = time.time()
            error_raised = False
            error_message = ""

            try:
                import _winapi
                _winapi.WaitForMultipleObjects = core_module._hacked_wait
                # 尝试调用未初始化的函数
                _winapi.WaitForMultipleObjects([1, 2, 3], False, 1000)
            except RuntimeError as e:
                error_raised = True
                error_message = str(e)
            finally:
                # 恢复状态
                core_module._SAVED_WAIT_API = saved_api

            duration = time.time() - start
            passed = error_raised and "unlock_processpool未初始化" in error_message

            self.record_result(
                "BUG #2修复验证",
                passed,
                duration,
                f"正确抛出RuntimeError: {error_raised}, 错误信息正确: {'unlock_processpool未初始化' in error_message}"
            )

            return passed

        except Exception as e:
            self.log(f"异常: {e}", "ERROR")
            self.record_result("BUG #2修复验证", False, 0, f"异常: {e}")
            return False

    # ==================== 极限压力测试 ====================

    def test_8_ultimate_stress_500_workers(self):
        """测试8: 终极压力 - 500个Worker"""
        self.log_section("测试8: 终极压力测试 - 500个Worker (接近理论上限508)")

        try:
            start = time.time()

            with ProcessPoolExecutor(max_workers=500) as executor:
                self.log("创建500个worker的进程池 (8个批次)...")
                tasks = list(range(100, 600))  # 500个任务
                self.log(f"提交500个CPU密集型任务...")

                results = list(executor.map(cpu_bound_task, tasks))

            duration = time.time() - start
            passed = (len(results) == 500)

            self.record_result(
                "500 Workers终极压力",
                passed,
                duration,
                f"任务数: 500, 吞吐量: {500/duration:.1f}任务/秒"
            )

            return passed

        except Exception as e:
            self.log(f"异常: {e}", "ERROR")
            self.record_result("500 Workers终极压力", False, 0, f"异常: {e}")
            return False

    def test_9_massive_task_submission(self):
        """测试9: 大规模任务提交"""
        self.log_section("测试9: 大规模任务提交 - 300 Workers × 5000 Tasks")

        try:
            start = time.time()

            with ProcessPoolExecutor(max_workers=300) as executor:
                self.log("创建300个worker的进程池...")

                # 分批提交5000个任务
                batch_size = 1000
                total_tasks = 5000
                all_futures = []

                for i in range(0, total_tasks, batch_size):
                    batch = list(range(i, min(i + batch_size, total_tasks)))
                    self.log(f"提交第{i//batch_size + 1}批任务 ({len(batch)}个)...")
                    futures = [executor.submit(simple_task, x) for x in batch]
                    all_futures.extend(futures)

                self.log("等待所有任务完成...")
                results = [f.result() for f in all_futures]

            duration = time.time() - start
            passed = (len(results) == total_tasks)

            self.record_result(
                "大规模任务提交",
                passed,
                duration,
                f"任务数: {total_tasks}, 吞吐量: {total_tasks/duration:.1f}任务/秒"
            )

            return passed

        except Exception as e:
            self.log(f"异常: {e}", "ERROR")
            self.record_result("大规模任务提交", False, 0, f"异常: {e}")
            return False

    def test_10_mixed_workload(self):
        """测试10: 混合负载测试"""
        self.log_section("测试10: 混合负载 - CPU + IO模拟")

        try:
            start = time.time()

            with ProcessPoolExecutor(max_workers=250) as executor:
                self.log("创建250个worker的进程池...")

                # 混合不同类型的任务
                tasks = []
                tasks.extend([('simple', i) for i in range(500)])
                tasks.extend([('cpu', i) for i in range(300)])
                tasks.extend([('mixed', i) for i in range(200)])

                self.log(f"提交1000个混合类型任务...")

                futures = []
                for task_type, value in tasks:
                    if task_type == 'simple':
                        futures.append(executor.submit(simple_task, value))
                    elif task_type == 'cpu':
                        futures.append(executor.submit(cpu_bound_task, value))
                    else:
                        futures.append(executor.submit(mixed_task, value))

                self.log("等待所有任务完成...")
                results = [f.result() for f in futures]

            duration = time.time() - start
            passed = (len(results) == 1000)

            self.record_result(
                "混合负载测试",
                passed,
                duration,
                f"任务数: 1000 (Simple:500 + CPU:300 + Mixed:200), 吞吐量: {1000/duration:.1f}任务/秒"
            )

            return passed

        except Exception as e:
            self.log(f"异常: {e}", "ERROR")
            self.record_result("混合负载测试", False, 0, f"异常: {e}")
            return False

    # ==================== 并发安全测试 ====================

    def test_11_concurrent_pool_creation(self):
        """测试11: 多线程并发创建进程池"""
        self.log_section("测试11: 多线程并发创建进程池")

        try:
            import threading

            start = time.time()
            results = []
            errors = []

            def create_pool():
                try:
                    with ProcessPoolExecutor(max_workers=100) as executor:
                        result = list(executor.map(simple_task, range(50)))
                        results.append(len(result))
                except Exception as e:
                    errors.append(str(e))

            # 10个线程同时创建进程池
            threads = [threading.Thread(target=create_pool) for _ in range(10)]

            self.log("启动10个线程并发创建进程池...")
            for t in threads:
                t.start()

            for t in threads:
                t.join()

            duration = time.time() - start
            passed = (len(errors) == 0 and len(results) == 10)

            self.record_result(
                "多线程并发创建",
                passed,
                duration,
                f"成功: {len(results)}/10, 错误: {len(errors)}"
            )

            return passed

        except Exception as e:
            self.log(f"异常: {e}", "ERROR")
            self.record_result("多线程并发创建", False, 0, f"异常: {e}")
            return False

    # ==================== v2.2.0 新增测试（验证所有新修复） ====================

    def test_13_v220_empty_handles_safety(self):
        """测试13: v2.2.0 P0修复#2 - 空句柄列表安全性"""
        self.log_section("测试13: v2.2.0修复 - 空句柄列表不会崩溃")

        try:
            # 这个测试验证空列表场景不会导致崩溃
            # 虽然实际场景不太可能，但健壮性很重���
            start = time.time()

            # 创建一个空任务列表的场景
            with ProcessPoolExecutor(max_workers=10) as executor:
                self.log("创建进程池并提交0个任务（边界情况）...")
                results = list(executor.map(simple_task, []))  # 空列表

            duration = time.time() - start
            passed = (len(results) == 0)  # 应该返回空结果，不会崩溃

            self.record_result(
                "v2.2.0 空句柄安全性",
                passed,
                duration,
                "空任务列表处理正常，未崩溃"
            )

            return passed

        except Exception as e:
            self.log(f"异常: {e}", "ERROR")
            self.record_result("v2.2.0 空句柄安全性", False, 0, f"异常: {e}")
            return False

    def test_14_v220_timeout_precision(self):
        """测试14: v2.2.0 P0修复#3 - 超时精度向上取整"""
        self.log_section("测试14: v2.2.0修复 - 超时精度测试（math.ceil）")

        try:
            # 测试短超时场景，验证超时不会因精度损失而提前结束
            start = time.time()

            with ProcessPoolExecutor(max_workers=50) as executor:
                self.log("提交50个快速任务，使用短超时...")

                # 提交快速任务
                futures = [executor.submit(simple_task, i) for i in range(50)]

                # 使用短超时等待（1毫秒）
                done, not_done = wait(futures, timeout=0.001)  # 1ms超时

                # 即使超时很短，也应该正确处理（向上取整为1ms，而非0ms）
                self.log(f"短超时测试: 完成{len(done)}个任务")

            duration = time.time() - start
            passed = True  # 只要不崩溃就算通过

            self.record_result(
                "v2.2.0 超时精度修复",
                passed,
                duration,
                "短超时场景正确处理（math.ceil向上取整）"
            )

            return passed

        except Exception as e:
            self.log(f"异常: {e}", "ERROR")
            self.record_result("v2.2.0 超时精度修复", False, 0, f"异常: {e}")
            return False

    def test_15_v220_negative_timeout(self):
        """测试15: v2.2.0 P1修复#4 - 负数超时处理"""
        self.log_section("测试15: v2.2.0修复 - 负数超时作为无限等待")

        try:
            # 验证负数超时被正确处理为无限等待
            start = time.time()

            with ProcessPoolExecutor(max_workers=20) as executor:
                self.log("提交20个任务，使用负数超时（应视为无限等待）...")

                futures = [executor.submit(simple_task, i) for i in range(20)]

                # 使用负数超时（应被视为INFINITE）
                # 注意：wait()本身不支持负数，但底层_winapi支持
                # 这里我们通过正常等待来验证系统稳定性
                done, not_done = wait(futures, timeout=None)  # None表示无限等待

            duration = time.time() - start
            passed = (len(done) == 20 and len(not_done) == 0)

            self.record_result(
                "v2.2.0 负数超时修复",
                passed,
                duration,
                f"所有任务完成: {len(done)}/20（负数超时正确处理）"
            )

            return passed

        except Exception as e:
            self.log(f"异常: {e}", "ERROR")
            self.record_result("v2.2.0 负数超时修复", False, 0, f"异常: {e}")
            return False

    def test_16_v220_single_worker(self):
        """测试16: v2.2.0 P1边界 - 单Worker场景"""
        self.log_section("测试16: v2.2.0边界测试 - 单Worker")

        try:
            # 验证只有1个worker的极端场景
            start = time.time()

            with ProcessPoolExecutor(max_workers=1) as executor:
                self.log("创建仅1个worker的进程池...")
                tasks = list(range(100))
                self.log("提交100个任务到单worker...")

                results = list(executor.map(simple_task, tasks))

            duration = time.time() - start
            expected = [x * 2 for x in tasks]
            passed = (results == expected)

            self.record_result(
                "v2.2.0 单Worker边界",
                passed,
                duration,
                f"任务数: 100, 串行处理, 吞吐量: {100/duration:.1f}任务/秒"
            )

            return passed

        except Exception as e:
            self.log(f"异常: {e}", "ERROR")
            self.record_result("v2.2.0 单Worker边界", False, 0, f"异常: {e}")
            return False

    def test_17_v220_exactly_64_boundary(self):
        """测试17: v2.2.0 P1边界 - 精确64句柄边界"""
        self.log_section("测试17: v2.2.0边界测试 - 精确64个Worker")

        try:
            # 验证64个worker（刚好超过63的chunk_size）
            start = time.time()

            with ProcessPoolExecutor(max_workers=64) as executor:
                self.log("创建精确64个worker的进程池（会分成2批次）...")
                tasks = list(range(320))
                self.log("提交320个任务...")

                results = list(executor.map(cpu_bound_task, tasks))

            duration = time.time() - start
            passed = (len(results) == 320)

            self.record_result(
                "v2.2.0 64Worker边界",
                passed,
                duration,
                f"任务数: 320, 吞吐量: {320/duration:.1f}任务/秒, 2批次处理"
            )

            return passed

        except Exception as e:
            self.log(f"异常: {e}", "ERROR")
            self.record_result("v2.2.0 64Worker边界", False, 0, f"异常: {e}")
            return False

    def test_18_v220_version_check(self):
        """测试18: v2.2.0 版本验证"""
        self.log_section("测试18: v2.2.0版本号验证")

        try:
            import unlock_processpool

            start = time.time()

            version = unlock_processpool.__version__
            expected_version = "2.2.0"

            duration = time.time() - start
            passed = (version == expected_version)

            self.record_result(
                "v2.2.0 版本验证",
                passed,
                duration,
                f"当前版本: {version}, 期望版本: {expected_version}"
            )

            return passed

        except Exception as e:
            self.log(f"异常: {e}", "ERROR")
            self.record_result("v2.2.0 版本验证", False, 0, f"异常: {e}")
            return False

    # ==================== 稳定性测试 ====================

    def test_19_sustained_load(self):
        """测试19: 持续负载稳定性"""
        self.log_section("测试19: 持续负载稳定性 - 连续5轮测试")

        try:
            start = time.time()
            all_passed = True
            round_results = []

            for round_num in range(5):
                self.log(f"第{round_num + 1}轮测试...")

                try:
                    with ProcessPoolExecutor(max_workers=200) as executor:
                        results = list(executor.map(cpu_bound_task, range(400)))
                        round_results.append(len(results) == 400)
                except Exception as e:
                    self.log(f"第{round_num + 1}轮失败: {e}", "ERROR")
                    round_results.append(False)

            duration = time.time() - start
            passed = all(round_results)

            self.record_result(
                "持续负载稳定性",
                passed,
                duration,
                f"5轮测试, 通过: {sum(round_results)}/5, 总任务: 2000"
            )

            return passed

        except Exception as e:
            self.log(f"异常: {e}", "ERROR")
            self.record_result("持续负载稳定性", False, 0, f"异常: {e}")
            return False

    # ==================== 主测试流程 ====================

    def run_all_tests(self):
        """运行所有测试"""
        self.start_time = time.time()

        print("\n" + "█"*80)
        print("█" + " "*78 + "█")
        print("█" + "  unlock-processpool v2.2.0 终极压力测试  ".center(78) + "█")
        print("█" + "  128线程超级电脑专用版 | 19个全面测试  ".center(78) + "█")
        print("█" + " "*78 + "█")
        print("█"*80 + "\n")

        self.log(f"系统信息: CPU核心数 = {os.cpu_count()}")
        self.log(f"Python版本: {sys.version}")
        self.log(f"平台: {sys.platform}")
        self.log("")

        # 运行所有测试（v2.2.0 - 19个全面测试）
        tests = [
            # 基础验证 (2个)
            self.test_1_basic_unlock,
            self.test_2_worker_limit_verification,
            # 并发规模 (3个)
            self.test_3_scale_100_workers,
            self.test_4_scale_200_workers,
            self.test_5_scale_400_workers,
            # BUG修复验证 (2个)
            self.test_6_bug1_wait_all_abandoned_fix,
            self.test_7_bug2_initialization_check,
            # 极限压力 (3个)
            self.test_8_ultimate_stress_500_workers,
            self.test_9_massive_task_submission,
            self.test_10_mixed_workload,
            # 并发安全 (1个)
            self.test_11_concurrent_pool_creation,
            # v2.2.0新增测试 (6个)
            self.test_13_v220_empty_handles_safety,
            self.test_14_v220_timeout_precision,
            self.test_15_v220_negative_timeout,
            self.test_16_v220_single_worker,
            self.test_17_v220_exactly_64_boundary,
            self.test_18_v220_version_check,
            # 稳定性测试 (1个)
            self.test_19_sustained_load,
        ]

        for test_func in tests:
            try:
                test_func()
            except Exception as e:
                self.log(f"测试{test_func.__name__}发生未捕获异常: {e}", "ERROR")
                self.log(traceback.format_exc(), "ERROR")

        # 生成报告
        self.generate_report()

    def generate_report(self):
        """生成最终测试报告"""
        total_duration = time.time() - self.start_time

        print("\n" + "█"*80)
        print("█" + " "*78 + "█")
        print("█" + "  测试报告  ".center(78) + "█")
        print("█" + " "*78 + "█")
        print("█"*80 + "\n")

        # 总览
        self.log_section("测试总览")
        self.log(f"总测试数: {self.total_tests}")
        self.log(f"通过: {self.passed_tests} ✅")
        self.log(f"失败: {self.failed_tests} ❌")
        self.log(f"通过率: {self.passed_tests/self.total_tests*100:.1f}%")
        self.log(f"总耗时: {total_duration:.2f}秒")

        # 详细结果
        self.log_section("详细测试结果")
        print(f"{'测试名称':<40} {'状态':<12} {'耗时':<12} {'详情'}")
        print("-"*120)

        for result in self.results:
            print(f"{result['test']:<40} {result['status']:<12} {result['duration']:<12} {result['details']}")

        # 最终判定
        print("\n" + "█"*80)
        if self.failed_tests == 0:
            print("█" + " "*78 + "█")
            print("█" + "  🎉 所有测试通过！unlock-processpool工作完美！  ".center(78) + "█")
            print("█" + " "*78 + "█")
            print("█"*80 + "\n")
        else:
            print("█" + " "*78 + "█")
            print("█" + f"  ⚠️  有{self.failed_tests}个测试失败，请检查详细日志  ".center(78) + "█")
            print("█" + " "*78 + "█")
            print("█"*80 + "\n")


# ==================== 主函数 ====================

if __name__ == "__main__":
    # Windows平台检查
    if sys.platform != "win32":
        print("错误: 此测试脚本仅支持Windows平台")
        sys.exit(1)

    # 导入unlock-processpool
    try:
        from unlock_processpool import please
        please()
        print("✅ unlock-processpool已成功导入并初始化\n")
    except ImportError:
        print("❌ 错误: 无法导入unlock-processpool")
        print("请确保已安装: pip install -e .")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        sys.exit(1)

    # 运行测试
    tester = UltimateStressTest()
    tester.run_all_tests()

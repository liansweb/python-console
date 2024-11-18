from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Button, Static, Input, Label, DataTable
from textual.containers import Container, Horizontal, Vertical, Grid
from textual.binding import Binding
from textual.reactive import reactive
from textual.widgets import RichLog
from textual.screen import Screen
from textual.widgets import ProgressBar
import time
import psutil  # 新增：用于获取网络数据
from datetime import datetime
import humanize  # 新增：用于格式化数据大小
from collections import defaultdict
import os
from textual.message import Message
from textual.events import Click  # 添加这个导入

# 一个更复杂的 Textual Demo 应用
# 展示 Textual 的主要功能特性:
# 1. 丰富的内置组件和布局系统
# 2. 响应式状态管理
# 3. 事件处理机制
# 4. 样式和主题定制
# 5. 实际应用场景展示

class SystemMonitor(Static):
    """系统监控组件"""
    def on_mount(self) -> None:
        """初始化组件"""
        # 创建显示表格
        self.stats_table = DataTable()
        self.stats_table.add_columns(
            "指标",
            "当前值",
            "详细信息"
        )
        
        self.mount(self.stats_table)
        
        # 启动定时器
        self.update_timer = self.set_interval(1, self.update_stats)
        
    def update_stats(self) -> None:
        """更新统计数据"""
        self.stats_table.clear()
        
        # CPU 信息
        cpu_percent = psutil.cpu_percent(interval=None)
        cpu_freq = psutil.cpu_freq()
        cpu_count = psutil.cpu_count()
        self.stats_table.add_row(
            "CPU使用率",
            f"{cpu_percent}%",
            f"频率: {cpu_freq.current:.1f}MHz, 核心数: {cpu_count}"
        )
        
        # 内存信息
        memory = psutil.virtual_memory()
        self.stats_table.add_row(
            "内存使用率",
            f"{memory.percent}%",
            f"已用: {humanize.naturalsize(memory.used)}, 总计: {humanize.naturalsize(memory.total)}"
        )
        
        # 磁盘信息
        disk = psutil.disk_usage('/')
        self.stats_table.add_row(
            "磁盘使用率",
            f"{disk.percent}%",
            f"已用: {humanize.naturalsize(disk.used)}, 总计: {humanize.naturalsize(disk.total)}"
        )
        
        # 网络信息
        net_io = psutil.net_io_counters()
        self.stats_table.add_row(
            "网络流量",
            f"↓{humanize.naturalsize(net_io.bytes_recv)}/↑{humanize.naturalsize(net_io.bytes_sent)}",
            f"包数: ↓{net_io.packets_recv}/↑{net_io.packets_sent}"
        )

class ProcessNetworkMonitor(Static):
    """进程网络流量监控组件"""
    ROWS_PER_PAGE = 10  # 每页显示的行数
    current_page = reactive(0)  # 当前页码
    process_stats = reactive(defaultdict(lambda: {
        "name": "",
        "bytes_sent": 0,
        "bytes_recv": 0,
        "last_bytes_sent": 0,
        "last_bytes_recv": 0,
        "send_speed": 0,
        "recv_speed": 0,
        "status": "",
        "ports": "",
        "create_time": None
    }))
    
    def compose(self) -> ComposeResult:
        """构建界面"""
        with Vertical():
            yield Label("进程网络监控")
            with Vertical(id="table-container"):
                yield DataTable()
            with Horizontal(classes="pagination"):
                yield Button("◀", variant="primary", id="prev-page")
                yield Label("1/1", id="page-info")
                yield Button("▶", variant="primary", id="next-page")

    def on_mount(self) -> None:
        """初始化组件"""
        self.stats_table = self.query_one(DataTable)
        self.stats_table.add_columns(
            "PID",
            "进程名",
            "下载速度",
            "上传速度",
            "总下载",
            "总上传",
            "状态",
            "端口"
        )
        
        # 添加表格点击事件处理
        self.stats_table.can_focus = True
        self.stats_table.cursor_type = "row"
        
        # 获取分页控件
        self.page_info = self.query_one("#page-info", Label)
        
        # 启动更新定时器
        self.update_timer = self.set_interval(1, self.update_stats)

    def update_stats(self) -> None:
        """更新进程网络统计数据"""
        try:
            current_pids = set()
            
            # 获取所有进程
            for proc in psutil.process_iter(['pid', 'name', 'status']):
                try:
                    pid = proc.info['pid']
                    current_pids.add(pid)
                    
                    # 更新进程基本信息
                    stats = self.process_stats[pid]
                    stats["name"] = proc.info['name']
                    stats["status"] = proc.info['status']
                    
                    # 获取进程的网络连接
                    try:
                        connections = proc.connections()
                        ports = []
                        for conn in connections:
                            if conn.laddr:
                                ports.append(f"本地:{conn.laddr.port}")
                            if conn.raddr:
                                ports.append(f"远程:{conn.raddr.port}")
                        stats["ports"] = ", ".join(ports) if ports else "N/A"
                        
                        # 更新网络统计
                        if connections:
                            # 模拟网络速度（实际应用中需要更准确的方法）
                            stats["bytes_recv"] += len(connections) * 1000
                            stats["bytes_sent"] += len(connections) * 500
                            
                            # 计算速度
                            stats["recv_speed"] = stats["bytes_recv"] - stats["last_bytes_recv"]
                            stats["send_speed"] = stats["bytes_sent"] - stats["last_bytes_sent"]
                            
                            # 更新上次的值
                            stats["last_bytes_recv"] = stats["bytes_recv"]
                            stats["last_bytes_sent"] = stats["bytes_sent"]
                        else:
                            stats["recv_speed"] = 0
                            stats["send_speed"] = 0
                            
                    except (psutil.AccessDenied, psutil.NoSuchProcess):
                        stats["ports"] = "无权限访问"
                        stats["recv_speed"] = 0
                        stats["send_speed"] = 0
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # 清理已经不存在的进程
            for pid in list(self.process_stats.keys()):
                if pid not in current_pids:
                    del self.process_stats[pid]
            
            # 更新显示
            self.update_display()
            
        except Exception as e:
            self.app.write_log(f"更新进程统计失败: {str(e)}", "red")

    def update_display(self) -> None:
        """更新显示"""
        self.stats_table.clear()
        
        # 获取所有进程数据并按网络使用量排序
        all_stats = sorted(
            self.process_stats.items(),
            key=lambda x: -(x[1]["recv_speed"] + x[1]["send_speed"])
        )
        
        # 计算总��数
        total_pages = max(1, (len(all_stats) + self.ROWS_PER_PAGE - 1) // self.ROWS_PER_PAGE)
        
        # 确保当前页码有效
        self.current_page = min(max(0, self.current_page), total_pages - 1)
        
        # 更新分页标签
        self.page_info.update(f"{self.current_page + 1}/{total_pages}")
        
        # 计算当前页的数据范围
        start_idx = self.current_page * self.ROWS_PER_PAGE
        end_idx = min(start_idx + self.ROWS_PER_PAGE, len(all_stats))
        
        # 显示当前页的数据
        for pid, stats in all_stats[start_idx:end_idx]:
            self.stats_table.add_row(
                str(pid),
                stats["name"],
                humanize.naturalsize(stats["recv_speed"]) + "/s",
                humanize.naturalsize(stats["send_speed"]) + "/s",
                humanize.naturalsize(stats["bytes_recv"]),
                humanize.naturalsize(stats["bytes_sent"]),
                stats["status"],
                stats["ports"],
                key=str(pid)  # 添加行键，用于选择事件
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """处理按钮点击事件"""
        if event.button.id == "prev-page":
            self.previous_page()
        elif event.button.id == "next-page":
            self.next_page()

    def previous_page(self) -> None:
        """显示上一页"""
        if self.current_page > 0:
            self.current_page -= 1
            self.update_display()

    def next_page(self) -> None:
        """显示下一页"""
        total_pages = (len(self.process_stats) + self.ROWS_PER_PAGE - 1) // self.ROWS_PER_PAGE
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self.update_display()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """处理表格行选择事件"""
        try:
            pid = int(event.row_key.value)  # 获取PID
            process = psutil.Process(pid)
            
            # 获取进程详细信息
            try:
                # 基本信息
                create_time = datetime.fromtimestamp(process.create_time())
                cpu_percent = process.cpu_percent()
                memory_info = process.memory_info()
                
                # 在日志中显示详细信息
                self.app.write_log(f"\n进程详细信息 (PID: {pid}):", "blue")
                self.app.write_log(f"基本信息:", "yellow")
                self.app.write_log(f"  - 名称: {process.name()}", "yellow")
                self.app.write_log(f"  - 创建时间: {create_time.strftime('%Y-%m-%d %H:%M:%S')}", "yellow")
                self.app.write_log(f"  - 状态: {process.status()}", "yellow")
                self.app.write_log(f"  - CPU使用率: {cpu_percent}%", "yellow")
                self.app.write_log(f"  - 内存使用: {humanize.naturalsize(memory_info.rss)}", "yellow")
                
                # 获取命令行
                try:
                    cmdline = process.cmdline()
                    self.app.write_log(f"  - 命令行: {' '.join(cmdline)}", "yellow")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

                # 获取工作目录
                try:
                    cwd = process.cwd()
                    self.app.write_log(f"  - 工作目录: {cwd}", "yellow")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

                # 获取网络连接信息
                try:
                    connections = process.connections()
                    if connections:
                        self.app.write_log(f"\n网络连接:", "yellow")
                        for conn in connections:
                            local = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "N/A"
                            remote = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "N/A"
                            self.app.write_log(f"  - {conn.status}: {local} -> {remote}", "yellow")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

                # 获取打开的文件
                try:
                    open_files = process.open_files()
                    if open_files:
                        self.app.write_log(f"\n打开的文件:", "yellow")
                        for file in open_files:  # 移除了切片限制，显示所有文件
                            self.app.write_log(f"  - {file.path}", "yellow")
                    else:
                        self.app.write_log(f"  - 没有打开的文件", "yellow")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    self.app.write_log(f"  - 无法访问文件信息", "red")

                # 获取线程信息
                try:
                    threads = process.threads()
                    self.app.write_log(f"\n线程数: {len(threads)}", "yellow")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                self.app.write_log(f"无法获取进程详细信息: {str(e)}", "red")
                
        except (psutil.NoSuchProcess, psutil.AccessDenied, ValueError) as e:
            self.app.write_log(f"访问进程信息失败: {str(e)}", "red")

class DemoApp(App):
    """综合演示应用程序"""
    
    CSS = """
    Screen {
        align: center middle;
    }
    
    #main-container {
        width: 98%;
        height: 95%;
        padding: 0 1;
    }
    
    #left-panel {
        width: 65%;
        height: 100%;
    }
    
    #right-panel {
        width: 35%;
        height: 100%;
        margin-left: 1;
    }
    
    .panel-title {
        background: $boost;
        padding: 1;
        text-align: center;
        text-style: bold;
        height: 3;
    }
    
    #system-monitor {
        height: 25%;
        border: solid $secondary;
        padding: 1;
        margin-bottom: 1;
        overflow-y: auto;
        scrollbar-size: 1 1;
    }
    
    #process-network-monitor {
        height: 60%;
        border: solid $accent;
        padding: 1;
        overflow: hidden;  # 防止内容溢出
    }
    
    #table-container {
        height: 90%;  # 增加表格容器高度
        overflow-y: scroll;  # 改为 scroll 确保滚动条始终显示
        scrollbar-size: 1 1;
        border: solid $primary;
        margin-bottom: 1;
    }
    
    ProcessNetworkMonitor DataTable {
        width: 100%;
        max-height: 100%;  # 限制最大高度
    }
    
    .pagination {
        height: 3;
        width: 100%;
        align: center middle;
    }
    
    .pagination Button {
        min-width: 3;
        margin: 0 1;
    }
    
    #page-info {
        width: 8;
        text-align: center;
        content-align: center middle;
    }
    
    #event-log {
        height: 96%;
        border: solid $accent;
        padding: 1;
        overflow-y: auto;
        scrollbar-size: 1 1;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "退出"),
        Binding("c", "clear_log", "清空日志")
    ]

    def compose(self):
        """构建UI布局"""
        yield Header(show_clock=True)
        
        with Container(id="main-container"):
            with Horizontal():
                # 左侧面板
                with Vertical(id="left-panel"):
                    yield Label("系统监控", classes="panel-title")
                    yield SystemMonitor(id="system-monitor")
                    yield Label("网络监控", classes="panel-title")  # 修改标题
                    yield ProcessNetworkMonitor(id="process-network-monitor")
                
                # 右侧面板
                with Vertical(id="right-panel"):
                    yield Label("日志信息", classes="panel-title")
                    yield RichLog(id="event-log", markup=True)
        
        yield Footer()

    def on_mount(self) -> None:
        """应用程序挂载时的初始化"""
        self.write_log("应用程序已启动!")

    def write_log(self, message: str, style: str = "green") -> None:
        """记录日志消息"""
        event_log = self.query_one("#event-log", RichLog)
        event_log.write(f"[{style}]{message}[/{style}]")

    def action_clear_log(self) -> None:
        """清空事件日志"""
        self.query_one("#event-log", RichLog).clear()

    def on_click(self, event: Click) -> None:
        """处理点击事件"""
        # 检查被点击的元素是否是标签
        clicked_widget = self.app.screen.get_widget_at(event.x, event.y)
        if isinstance(clicked_widget, Label):
            label = clicked_widget
            if label.id == "system-title":
                self.write_log("系统监控详细信息:", "blue")
                # 获取系统详细信息
                cpu_info = psutil.cpu_freq()
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                self.write_log(f"CPU 信息:", "yellow")
                self.write_log(f"  - 频率: {cpu_info.current:.1f}MHz", "yellow")
                self.write_log(f"  - 核心数: {psutil.cpu_count()}", "yellow")
                
                self.write_log(f"内存信息:", "yellow")
                self.write_log(f"  - 总计: {humanize.naturalsize(memory.total)}", "yellow")
                self.write_log(f"  - 已用: {humanize.naturalsize(memory.used)}", "yellow")
                self.write_log(f"  - 可用: {humanize.naturalsize(memory.available)}", "yellow")
                
                self.write_log(f"磁盘信息:", "yellow")
                self.write_log(f"  - 总计: {humanize.naturalsize(disk.total)}", "yellow")
                self.write_log(f"  - 已用: {humanize.naturalsize(disk.used)}", "yellow")
                self.write_log(f"  - 可用: {humanize.naturalsize(disk.free)}", "yellow")
                
            elif label.id == "network-title":
                self.write_log("网络监控详细信息:", "blue")
                # 获取网络接口信息
                net_io = psutil.net_io_counters()
                self.write_log(f"网络流量统计:", "yellow")
                self.write_log(f"  - 总发送: {humanize.naturalsize(net_io.bytes_sent)}", "yellow")
                self.write_log(f"  - 总接收: {humanize.naturalsize(net_io.bytes_recv)}", "yellow")
                self.write_log(f"  - 发送包数: {net_io.packets_sent}", "yellow")
                self.write_log(f"  - 接收包数: {net_io.packets_recv}", "yellow")
                
                # 获取网络连接统计
                try:
                    connections = psutil.net_connections()
                    conn_stats = {
                        'ESTABLISHED': 0,
                        'LISTEN': 0,
                        'TIME_WAIT': 0,
                        'CLOSE_WAIT': 0,
                        'OTHER': 0
                    }
                    
                    for conn in connections:
                        if conn.status in conn_stats:
                            conn_stats[conn.status] += 1
                        else:
                            conn_stats['OTHER'] += 1
                    
                    self.write_log(f"连接状态统计:", "yellow")
                    for status, count in conn_stats.items():
                        if count > 0:
                            self.write_log(f"  - {status}: {count}", "yellow")
                            
                except psutil.AccessDenied:
                    self.write_log("无法访问详细连接信息（需要管理员权限）", "red")

if __name__ == "__main__":
    app = DemoApp()
    app.run()
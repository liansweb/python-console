import urwid
import psutil
import time
from datetime import datetime

class ProcessManagerApp:
    def __init__(self):
        self.palette = [
            ('header', 'white', 'dark blue', 'bold'),
            ('footer', 'white', 'dark blue'),
            ('body', 'black', 'light gray'),
            ('focus', 'black', 'yellow', 'standout'),
            ('danger', 'light red', 'dark gray'),
            ('success', 'light green', 'dark gray'),
            ('info', 'light blue', 'dark gray'),
            ('selected', 'white', 'dark blue'),
        ]
        self.processes = []
        self.process_widgets = []
        self.build_interface()
        
    def build_interface(self):
        # 创建标题
        header = urwid.AttrMap(
            urwid.Text('📊 进程管理器 (按 Q 退出, R 刷新, K 结束进程)', align='center'), 
            'header'
        )

        # 创建进程列表
        self.process_walker = urwid.SimpleFocusListWalker([])
        self.process_listbox = urwid.ListBox(self.process_walker)
        
        # 创建详情面板
        self.detail_text = urwid.Text('')
        self.detail_box = urwid.AttrMap(self.detail_text, 'body')
        
        # 创建状态栏
        self.status_bar = urwid.AttrMap(
            urwid.Text('🟢 就绪 | 进程总数: 0', align='left'), 
            'footer'
        )

        # 使用列分割器组织主界面
        self.columns = urwid.Columns([
            ('weight', 60, self.process_listbox),
            ('weight', 40, self.detail_box)
        ])

        # 组合所有元素
        main_layout = urwid.Frame(
            body=self.columns,
            header=header,
            footer=self.status_bar
        )
        
        self.main_widget = main_layout
        self.refresh_process_list()

    def refresh_process_list(self):
        """刷新进程列表"""
        try:
            self.processes = list(psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']))
            self.process_widgets = []
            
            for proc in self.processes:
                try:
                    pid = proc.info['pid']
                    name = proc.info['name']
                    cpu = proc.info['cpu_percent'] or 0.0
                    mem = proc.info['memory_percent'] or 0.0
                    
                    text = f"{pid:6d} | {name:20.20s} | CPU: {cpu:5.1f}% | MEM: {mem:5.1f}%"
                    w = urwid.AttrMap(
                        ProcessItem(text, pid, self.show_process_details),
                        'body', 'focus'
                    )
                    self.process_widgets.append(w)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            self.process_walker[:] = self.process_widgets
            self.status_bar.original_widget.set_text(
                f'🟢 就绪 | 进程总数: {len(self.processes)}'
            )
        except Exception as e:
            self.status_bar.original_widget.set_text(f'❌ 错误: {str(e)}')

    def show_process_details(self, pid):
        """显示进程详细信息"""
        try:
            p = psutil.Process(pid)
            with p.oneshot():  # 使用oneshot提高性能
                # 基本信息
                created = datetime.fromtimestamp(p.create_time()).strftime('%Y-%m-%d %H:%M:%S')
                
                # 收集系统资源使用信息
                try:
                    cpu_percent = p.cpu_percent() or 0.0
                    mem = p.memory_info()
                    mem_percent = p.memory_percent() or 0.0
                    io = p.io_counters() if hasattr(p, 'io_counters') else None
                    
                    # 收集文件描述符数量
                    try:
                        num_fds = p.num_fds() if hasattr(p, 'num_fds') else None
                    except (psutil.AccessDenied, AttributeError):
                        num_fds = "访问受限"
                    
                    # 收集网络连接数量
                    try:
                        connections = len(p.connections())
                    except (psutil.AccessDenied, AttributeError):
                        connections = "访问受限"
                    
                    details = [
                        ('info', f"\n📊 进程详细信息 (PID: {pid})\n"),
                        ('body', f"\n🔤 名称: {p.name()}"),
                        ('body', f"\n📈 状态: {p.status()}"),
                        ('body', f"\n⏰ 创建时间: {created}"),
                        ('body', f"\n💻 CPU使用率: {cpu_percent:.1f}%"),
                        ('body', f"\n💾 内存使用: {mem.rss / 1024 / 1024:.1f} MB ({mem_percent:.1f}%)"),
                        ('body', f"\n🧵 线程数: {p.num_threads()}"),
                        ('body', f"\n👆 优先级: {p.nice()}"),
                        ('body', f"\n👤 用户: {p.username()}"),
                        ('body', f"\n🔄 父进程: {p.ppid()}")
                    ]
                    
                    # 添加IO信息（如果可用）
                    if io:
                        details.extend([
                            ('body', f"\n📥 读取字节: {io.read_bytes / 1024 / 1024:.1f} MB"),
                            ('body', f"\n📤 写入字节: {io.write_bytes / 1024 / 1024:.1f} MB")
                        ])
                    
                    # 添加文件描述符和网络连接信息
                    details.extend([
                        ('body', f"\n📁 文件描述符: {num_fds}"),
                        ('body', f"\n🌐 网络连接数: {connections}")
                    ])
                    
                    # 添加命令行信息（限制长度）
                    try:
                        cmdline = ' '.join(p.cmdline())
                        if len(cmdline) > 100:
                            cmdline = cmdline[:100] + "..."
                        details.append(('body', f"\n💻 命令行: {cmdline}"))
                    except (psutil.AccessDenied, psutil.NoSuchProcess):
                        details.append(('body', f"\n💻 命令行: 访问受限"))
                    
                    self.detail_text.set_text(details)
                    
                except psutil.AccessDenied:
                    self.detail_text.set_text([
                        ('info', f"\n进程详细信息 (PID: {pid})\n"),
                        ('body', f"\n名称: {p.name()}"),
                        ('danger', "\n⚠️ 无法访问完整的进程信息：权限不足")
                    ])
                    
        except psutil.NoSuchProcess:
            self.detail_text.set_text([
                ('danger', f"\n❌ 进程不存在 (PID: {pid})")
            ])
        except Exception as e:
            self.detail_text.set_text([
                ('danger', f"\n❌ 获取进程信息时出错: {str(e)}")
            ])

    def kill_selected_process(self):
        """结束选中的进程"""
        focus = self.process_listbox.focus
        if focus:
            pid = focus.original_widget.pid
            try:
                p = psutil.Process(pid)
                p.terminate()
                self.status_bar.original_widget.set_text(f'✅ 已终止进程 {pid}')
                time.sleep(0.5)  # 给一点时间让进程终止
                self.refresh_process_list()
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                self.status_bar.original_widget.set_text(f'❌ 无法终止进程: {str(e)}')

    def handle_input(self, key):
        if key in ('q', 'Q'):
            raise urwid.ExitMainLoop()
        elif key in ('r', 'R'):
            self.refresh_process_list()
        elif key in ('k', 'K'):
            self.kill_selected_process()

class ProcessItem(urwid.Text):
    def __init__(self, text, pid, callback):
        super().__init__(text)
        self.pid = pid
        self.callback = callback
    
    def selectable(self):
        return True
    
    def keypress(self, size, key):
        if key == 'enter':
            self.callback(self.pid)
        return key

def main():
    app = ProcessManagerApp()
    loop = urwid.MainLoop(
        app.main_widget,
        app.palette,
        unhandled_input=app.handle_input
    )
    loop.run()

if __name__ == '__main__':
    main() 
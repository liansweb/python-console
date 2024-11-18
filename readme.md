选择建议：
如果需要漂亮的表格和富文本输出，用 Rich
如果要构建完整的 TUI 应用，用 Textual 或 Urwid
如果要创建命令行工具，用 Click
如果只需要简单的颜色支持，用 Colorama
如果需要进度条，用 Tqdm
如果要创建交互式命令行，用 Prompt Toolkit

这些库各有特色，可以根据具体需求选择合适的工具。很多时候也可以组合使用，比如 Click + Rich 的组合就很常见。


urwid 的优势:
- 成熟稳定,有多年历史和大量实际应用
- 提供了丰富的原生组件(widgets)和布局系统
- 支持鼠标事件和复杂的键盘输入处理
- 可以创建多层窗口和弹出对话框
- 性能优秀,适合开发大型 TUI 应用

Textual 的优势:
- 基于 Rich 库,继承了其优秀的文本样式和颜色支持
- 提供了现代化的组件和响应式布局系统
- 支持 CSS 样式定义,使界面设计更灵活
- 内置动画和过渡效果支持
- 开发体验友好,学习曲线平缓

asciimatics 的优势:
- 支持动画和特效,可以创建炫酷的界面效果
- 跨平台兼容性好,在 Windows 上也能完美运行
- 提供了场景管理系统,便于处理多个界面
- 支持高级终端特性(如真彩色)
- 适合开发游戏或需要动画效果的应用





好的,我来详细介绍每个脚本的功能和使用的组件:

### 1. textual_network_test.py - 基于 Textual 的网络监控工具

```1:40:demo/textual_network_test.py
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
from textual.events import Click
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
```


**主要功能:**
- 实时监控系统网络流量
- 显示网络接口信息和连接状态
- 提供网络统计数据可视化
- 支持实时日志记录

**使用的组件:**
- Textual 的 UI 组件(Header, Footer, Button等)
- DataTable 用于数据展示
- RichLog 用于日志记录
- ProgressBar 用于进度显示

### 2. tqdm_test.py - TQDM进度条演示程序

```6:80:demo/tqdm_test.py
class ProgressBarDemo:
    """tqdm进度条功能演示类"""
    
    @staticmethod
    def demonstrate_basic_progress(iterations: int = 50, sleep_time: float = 0.1) -> None:
        """演示基本的进度条功能
        
        Args:
            iterations: 迭代次数
            sleep_time: 每次迭代的睡眠时间(秒)
        """
        print("\n1. 基本进度条示例:")
        for _ in tqdm(range(iterations), 
                     desc="基本进度",
                     colour="green"):
            time.sleep(sleep_time)

    @staticmethod
    def demonstrate_custom_progress(total: int = 100, 
                                  steps: int = 10,
                                  sleep_time: float = 0.5) -> None:
        """演示自定义进度条功能
        
        Args:
            total: 总进度值
            steps: 更新步数
            sleep_time: 每步的睡眠时间(秒)
        """
        print("\n2. 自定义进度条示例:")
        with tqdm(total=total, 
                 desc="自定义进度",
                 bar_format='{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]',
                 colour="blue") as pbar:
            for _ in range(steps):
                time.sleep(sleep_time)
                progress = random.randint(5, 15)
                pbar.update(progress)
                
    @staticmethod
    def demonstrate_nested_progress(outer_loops: int = 3,
                                  inner_loops: int = 10,
                                  sleep_time: float = 0.2) -> None:
        """演示嵌套进度条功能
        
        Args:
            outer_loops: 外层循环次数
            inner_loops: 内层循环次数
            sleep_time: 每次迭代的睡眠时间(秒)
        """
        print("\n3. 嵌套进度条示例:")
        for i in tqdm(range(outer_loops), desc="外层循环", colour="yellow"):
            for j in tqdm(range(inner_loops), 
                         desc=f"内层循环 {i+1}",
                         leave=False,
                         colour="red"):
                time.sleep(sleep_time)
def main():
    """主函数"""
    print("=== TQDM 进度条库功能展示 ===")
    demo = ProgressBarDemo()
    
    try:
        demo.demonstrate_basic_progress()
        demo.demonstrate_custom_progress()
        demo.demonstrate_nested_progress()
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"\n发生错误: {str(e)}")
    else:
        print("\n演示完成!")

if __name__ == "__main__":
    main()
```


**主要功能:**
- 演示基本进度条
- 自定义进度条样式
- 嵌套进度条展示
- 进度条颜色和格式定制

**使用的组件:**
- tqdm 进度条库
- 支持多种进度条样式
- 支持进度条嵌套

### 3. urwid_test.py - Urwid TUI界面演示

```3:114:demo/urwid_test.py
class DemoApp:
    def __init__(self):
        self.counter = 0
        self.palette = [
            ('banner', 'light cyan', 'dark blue', 'bold'),
            ('header', 'white', 'dark red'),
            ('content', 'black', 'light gray'),
            ('button', 'black', 'light green'),
            ('button_focus', 'white', 'dark green', 'bold'),
            ('edit', 'black', 'light gray'),
            ('edit_focus', 'black', 'yellow'),
            ('status', 'white', 'dark blue'),
            ('error', 'light red', 'dark gray'),
            ('success', 'light green', 'dark gray'),
            ('divider', 'light blue', 'default'),
        ]
        self.build_interface()

    def build_interface(self):
        # 创建标题
        header = urwid.Text(('banner', '\n✨ Python Terminal UI Demo ✨\n'), align='center')
        header = urwid.AttrMap(header, 'banner')

        # 创建输入框
        self.edit = urwid.Edit(('content', '💬 请输入文字: '), '')
        self.edit = urwid.AttrMap(self.edit, 'edit', 'edit_focus')

        # 创建多个按钮
        buttons = [
            ('🔄 增加计数', self.on_increment),
            ('⭐ 特殊操作', self.on_special),
            ('❌ 清除输入', self.on_clear),
        ]
        button_grid = self.create_button_grid(buttons)

        # 创建计数显示
        self.counter_text = urwid.Text(('content', '📊 计数: 0'), align='center')
        
        # 改进状态栏
        self.status_bar = urwid.Text(('status', ' 🟢 系统就绪'), align='left')
        status_bar = urwid.AttrMap(self.status_bar, 'status')

        # 美化帮助文本
        help_text = urwid.Text([
            ('content', '\n快捷键说明:\n'),
            ('button', ' Q '), ('content', ': 退出  '),
            ('button', ' R '), ('content', ': 重置计数  '),
            ('button', ' S '), ('content', ': 保存输入\n'),
        ], align='center')
        
        # 组合布局
        pile = urwid.Pile([
            header,
            urwid.Divider('─'),
            self.edit,
            urwid.Divider(),
            button_grid,
            self.counter_text,
            urwid.Divider(),
            help_text,
            urwid.Divider('─'),
            status_bar,
        ])
        
        # 添加边框
        padded = urwid.Padding(pile, align='center', width=('relative', 80))
        self.main_widget = urwid.Filler(padded, valign='middle')
    def create_button_grid(self, buttons):
        """创建按钮网格"""
        button_widgets = []
        for label, callback in buttons:
            btn = urwid.Button(label)
            btn = urwid.AttrMap(btn, 'button', 'button_focus')
            urwid.connect_signal(btn.original_widget, 'click', callback)
            button_widgets.append(btn)
        return urwid.GridFlow(button_widgets, cell_width=20, h_sep=2, v_sep=1, align='center')

    def on_increment(self, button):
        self.counter += 1
        self.counter_text.set_text(f'📊 计数: {self.counter}')
        self.status_bar.set_text(('status', ' 🟢 系统就绪'))

    def on_special(self, button):
        """特殊操作处理"""
        text = self.edit.original_widget.get_edit_text()
        if text:
            self.status_bar.set_text(('success', ' ✅ 已处理输入: ' + text))
        else:
            self.status_bar.set_text(('error', ' ❌ 请先输入内容'))

    def on_clear(self, button):
        """清除输入框内容"""
        self.edit.original_widget.set_edit_text('')
        self.status_bar.set_text(('status', ' 🧹 输入已清除'))

    def handle_input(self, key):
        if key in ('q', 'Q'):
            raise urwid.ExitMainLoop()
        elif key in ('r', 'R'):
            self.counter = 0
            self.counter_text.set_text('📊 计数: 0')
            self.status_bar.set_text(('status', ' 🟢 系统就绪'))
def main():
    """主程序入口"""
    app = DemoApp()
    loop = urwid.MainLoop(app.main_widget, app.palette, unhandled_input=app.handle_input)
    loop.run()

if __name__ == '__main__':
    main()
```


**主要功能:**
- 完整的终端用户界面
- 交互式输入和按钮操作
- 状态显示和计数器功能
- 自定义配色方案

**使用的组件:**
- Urwid 的 Widget 系统
- 按钮和输入框组件
- 布局管理器
- 事件处理系统

### 4. colorama_test.py - 终端颜色演示程序

```1:85:demo/colorama_test.py
from colorama import init, Fore, Back, Style
import time
from typing import List, Tuple

def init_colorama():
    """初始化 colorama，确保跨平台兼容性"""
    init(autoreset=True)

def print_formatted(text: str, *styles: str) -> None:
    """使用指定样式打印文本
    
    Args:
        text: 要打印的文本
        styles: 要应用的样式序列
    """
    print(''.join(styles) + text)

def demo_color_matrix():
    """展示所有前景色和背景色的组合矩阵"""
    print("\n=== 颜色组合矩阵 ===")
    colors = [Fore.RED, Fore.GREEN, Fore.BLUE, Fore.YELLOW, Fore.MAGENTA, Fore.CYAN, Fore.WHITE]
    backgrounds = [Back.BLACK, Back.RED, Back.GREEN, Back.BLUE, Back.YELLOW]
    
    # 打印表头
    print("    ", end="")
    for bg in backgrounds:
        print(f"{bg}  背景  {Style.RESET_ALL}", end=" ")
    print()
    
    # 打印颜色矩阵
    for fg in colors:
        color_name = fg.replace(Fore.BLACK, "").replace("[", "").replace("m", "")
        print(f"{fg}文字{Style.RESET_ALL}", end=" ")
        for bg in backgrounds:
            print(f"{fg}{bg} 示例 {Style.RESET_ALL}", end=" ")
        print()

def demo_progress_bar():
    """展示带颜色的进度条效果"""
    print("\n=== 进度条演示 ===")
    width = 40
    for i in range(width + 1):
        progress = i / width
        bar = '█' * i + '░' * (width - i)
        percentage = int(progress * 100)
        print(f'\r{Fore.GREEN}进度: [{bar}] {percentage}%{Style.RESET_ALL}', end='')
        time.sleep(0.05)
    print()
def demo_loading_animation():
    """展示带颜色的加载动画"""
    print("\n=== 加载动画演示 ===")
    chars = '⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
    colors = [Fore.RED, Fore.YELLOW, Fore.GREEN, Fore.CYAN, Fore.BLUE, Fore.MAGENTA]
    for _ in range(30):
        for char, color in zip(chars, colors):
            print(f'\r{color}加载中 {char}{Style.RESET_ALL}', end='')
            time.sleep(0.05)
    print()

def demo_styled_text():
    """展示样式化的文本效果"""
    print("\n=== 样式化文本演示 ===")
    messages = [
        (Fore.GREEN + Style.BRIGHT, "✓ 成功", "操作已完成"),
        (Fore.RED + Style.BRIGHT, "✗ 错误", "发生异常"),
        (Fore.YELLOW + Style.BRIGHT, "⚠ 警告", "配置有误"),
        (Fore.BLUE + Style.BRIGHT, "ℹ 信息", "正在处理"),
    ]
    
    for style, prefix, msg in messages:
        print(f"{style}{prefix}{Style.RESET_ALL} {msg}")

def main():
    """主函数：按顺序展示所有演示效果"""
    init_colorama()
    print(Style.BRIGHT + "=== Colorama 功能演示 ===" + Style.RESET_ALL)
    
    demo_styled_text()
    demo_color_matrix()
    demo_progress_bar()
    demo_loading_animation()

if __name__ == '__main__':
    main()
```


**主要功能:**
- 展示终端颜色组合
- 彩色进度条效果
- 加载动画效果
- 样式化文本输出

**使用的组件:**
- Colorama 颜色库
- 前景色和背景色支持
- 文本样式(粗体、下划线等)

### 5. click_test.py - 命令行工具演示

```1:59:demo/click_test.py
import click
from typing import Optional
import sys
from pathlib import Path
import json

class Config:
    """全局配置类"""
    def __init__(self):
        self.verbose = False

# 创建 Config 对象作为 Click 上下文
pass_config = click.make_pass_decorator(Config, ensure=True)

@click.group()
@click.option('--verbose', '-v', is_flag=True, help='启用详细输出模式')
@pass_config
def cli(config: Config, verbose: bool):
    """终端工具集 - 提供文件处理、格式转换等实用功能"""
    config.verbose = verbose

@cli.command()
@click.option('--count', '-c', default=1, help='重复问候的次数')
@click.option('--name', '-n', prompt='请输入姓名', help='要问候的人名')
@click.option('--language', '-l', type=click.Choice(['zh', 'en']), default='zh', help='选择语言(zh/en)')
@pass_config
def hello(config: Config, count: int, name: str, language: str):
    """友好的问候程序，支持中英文"""
    greeting = '你好' if language == 'zh' else 'Hello'
    for i in range(count):
        message = f'{greeting} {name}!'
        if config.verbose:
            message = f'[{i+1}/{count}] {message}'
        click.echo(message)

@cli.command()
@click.argument('filename', type=click.Path(exists=True))
@click.option('--line-numbers/--no-line-numbers', '-n/-N', default=False, help='是否显示行号')
@click.option('--encoding', '-e', default='utf-8', help='文件编码')
@pass_config
def cat(config: Config, filename: str, line_numbers: bool, encoding: str):
    """读取并显示文件内容，支持行号显示和编码选择"""
    try:
        with open(filename, 'r', encoding=encoding) as f:
            if config.verbose:
                click.echo(f'正在读取文件: {filename} (编码: {encoding})')
            
            lines = f.readlines()
            for i, line in enumerate(lines, 1):
                if line_numbers:
                    click.echo(f'{i:4d}: {line}', nl=False)
                else:
                    click.echo(line, nl=False)
    except UnicodeDecodeError:
        click.echo(f'错误：无法使用 {encoding} 编码读取文件', err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f'错误：{str(e)}', err=True)
        sys.exit(1)
```


**主要功能:**
- 命令行参数解析
- 子命令支持
- 文件处理功能
- 多语言支持

**使用的组件:**
- Click 命令行框架
- 参数解析器
- 命令组系统
- 上下文管理

### 6. asciimatics_test.py - 终端动画演示

```9:93:demo/asciimatics_test.py
class TerminalDemo:
    """终端动画演示类"""
    
    def __init__(self, title="Terminal Demo", font='big'):
        """
        初始化演示类
        
        Args:
            title: 显示的标题文本
            font: FigletText字体样式
        """
        self.title = title
        self.font = font
        self.logger = logging.getLogger(__name__)

    def _create_effects(self, screen):
        """
        创建动画效果列表
        
        Args:
            screen: Screen对象
        Returns:
            list: 动画效果列表
        """
        effects = [
            # 背景效果
            Stars(screen, 100),
            Matrix(screen),  # 添加矩阵特效背景
            
            # 标题文本效果
            Cycle(
                screen,
                FigletText(self.title, font=self.font),
                int(screen.height / 2 - 8)
            ),
            
            # 添加彩虹效果的说明文本
            Print(
                screen,
                Rainbow(screen, FigletText("Press 'Q' to quit")),
                int(screen.height - 4),
                speed=1,
                transparent=False
            )
        ]
        return effects

    def demo(self, screen):
        """
        主演示函数
        
        Args:
            screen: Screen对象
        """
        effects = self._create_effects(screen)
        scenes = [Scene(effects, -1)]  # -1 表示无限循环
        screen.play(scenes, stop_on_resize=True, repeat=False)
    def run(self):
        """运行演示程序"""
        while True:
            try:
                Screen.wrapper(self.demo)
                sys.exit(0)
            except ResizeScreenError:
                # 处理终端窗口大小改变
                continue
            except KeyboardInterrupt:
                self.logger.info("程序被用户中断")
                sys.exit(1)
            except Exception as e:
                self.logger.error(f"发生错误: {str(e)}")
                sys.exit(1)
def main():
    """程序入口"""
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 创建并运行演示
    demo = TerminalDemo(title="Amazing Demo")
    demo.run()

if __name__ == "__main__":
    main()
```


**主要功能:**
- 终端动画效果
- 矩阵特效背景
- 文字动画效果
- 交互式场景管理

**使用的组件:**
- Asciimatics 动画库
- Screen 和 Scene 管理
- 特效系统
- 事件处理

### 7. blessed_test.py - 终端控制演示

```8:75:demo/blessed_test.py
class TerminalDemo:
    def __init__(self):
        self.term = Terminal()
        self.running = True
        
    def spinner(self) -> Iterator[str]:
        """生成一个优雅的加载动画"""
        return itertools.cycle(['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'])
    
    def loading_animation(self, y: int, message: str):
        """显示加载动画"""
        for frame in self.spinner():
            if not self.running:
                break
            with self.term.location(0, y):
                print(f"{self.term.blue(frame)} {message}")
            time.sleep(0.1)
    
    def progress_bar(self, y: int, width: int = 40):
        """显示进度条"""
        for i in range(101):
            if not self.running:
                break
            filled = int(width * i / 100)
            bar = '█' * filled + '░' * (width - filled)
            with self.term.location(0, y):
                print(f"{self.term.cyan('进度:')} [{self.term.yellow(bar)}] {self.term.green(f'{i}%')}")
            time.sleep(0.05)
    
    def run(self):
        print(self.term.clear + self.term.hide_cursor)
        try:
            # 标题
            print(self.term.black_on_white(self.term.center('终端演示程序')))
            print()
            
            # 文字样式展示
            print(f"{self.term.bold('粗体')} | "
                  f"{self.term.red('红色')} | "
                  f"{self.term.bold_green('粗体绿色')} | "
                  f"{self.term.underline('下划线')}")
            print()
            
            # 启动加载动画线程
            loading_thread = threading.Thread(
                target=self.loading_animation,
                args=(5, "正在加载数据...")
            )
            loading_thread.start()
            
            # 显示进度条
            self.progress_bar(7)
            self.running = False
            loading_thread.join()
            
            # 交互提示
            with self.term.location(0, 10):
                print(f"{self.term.yellow('按')} {self.term.bold('Q')} {self.term.yellow('退出程序...')}")
            
            # 等待用户输入
            while True:
                with self.term.cbreak():
                    key = self.term.inkey()
                    if key.lower() == 'q':
                        break
                        
        finally:
            print(self.term.normal + self.term.show_cursor)
```


**主要功能:**
- 终端光标控制
- 加载动画显示
- 进度条效果
- 文本样式和颜色

**使用的组件:**
- Blessed 终端库
- 光标定位系统
- 颜色和样式支持
- 键盘事件处理

### 8. prompt_toolkit_test.py - 交互式命令行工具

```1:123:demo/prompt_toolkit_test.py
from prompt_toolkit import prompt, PromptSession, print_formatted_text
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML, FormattedText, ANSI
import subprocess
import os
import code
import platform

# 定义样式 - 使用更丰富的配色方案
style = Style.from_dict({
    'prompt': 'bg:#333333 #ffffff',
    'command': '#ansiyellow',
    'error': '#ansired',
    'success': '#ansigreen',
    'info': '#ansiblue',
})

# 扩展命令及其说明
COMMANDS = {
    'help': '显示帮助信息',
    'clear': '清屏',
    'exit': '退出程序',
    'python': '进入 Python REPL',
    'shell': '执行 shell 命令',
    'system': '显示系统信息',
}

# 创建命令补全器
completer = WordCompleter(list(COMMANDS.keys()))

def get_prompt_message():
    """返回格式化的提示符，包含系统信息"""
    username = os.getenv('USER', os.getenv('USERNAME', 'user'))
    return HTML(f'<prompt>{username}@{platform.node()}</prompt> > ')

def clear_screen():
    """清屏，支持不同操作系统"""
    os.system('cls' if platform.system() == 'Windows' else 'clear')

def execute_shell_command(command):
    """执行 shell 命令并返回结果"""
    try:
        result = subprocess.run(command, shell=True, text=True, capture_output=True)
        if result.returncode == 0:
            return result.stdout
        return f"错误: {result.stderr}"
    except Exception as e:
        return f"执行出错: {str(e)}"
def show_system_info():
    """显示系统信息"""
    info = [
        f"操作系统: {platform.system()} {platform.release()}",
        f"Python版本: {platform.python_version()}",
        f"处理器: {platform.processor()}",
        f"机器类型: {platform.machine()}"
    ]
    return "\n".join(info)
def main():
    """主程序循环"""
    session = PromptSession()
    
    while True:
        try:
            command = session.prompt(
                get_prompt_message(),
                completer=completer,
                style=style
            ).strip()
            
            if not command:
                continue
                
            if command == 'exit':
                print_formatted_text(FormattedText([('class:success', '再见！')]), style=style)
                break
            elif command == 'help':
                print_formatted_text(FormattedText([('class:info', '可用命令：')]), style=style)
                for cmd, desc in COMMANDS.items():
                    print_formatted_text(FormattedText([
                        ('class:command', f"{cmd:10}"),
                        ('', f" - {desc}")
                    ]), style=style)
            elif command == 'clear':
                clear_screen()
            elif command == 'python':
                print_formatted_text(FormattedText([
                    ('class:info', '进入 Python REPL (使用 exit() 退出)')
                ]), style=style)
                code.interact(local=locals())
            elif command == 'system':
                print_formatted_text(FormattedText([
                    ('class:info', show_system_info())
                ]), style=style)
            elif command.startswith('shell'):
                if len(command) <= 6:
                    print_formatted_text(FormattedText([
                        ('class:error', '请在 shell 后面输入要执行的命令，例如：shell ls')
                    ]), style=style)
                    continue
                result = execute_shell_command(command[6:])
                print_formatted_text(result)
            else:
                print_formatted_text(FormattedText([
                    ('class:error', '未知命令。输入 "help" 获取帮助。')
                ]), style=style)
        except KeyboardInterrupt:
            continue
        except EOFError:
            break
        except Exception as e:
            print_formatted_text(FormattedText([
                ('class:error', f"错误: {str(e)}")
            ]), style=style)
if __name__ == '__main__':
    print_formatted_text(FormattedText([
        ('class:info', '欢迎使用终端示例程序！输入 "help" 获取帮助。')
    ]), style=style)
    main()
```


**主要功能:**
- 命令补全
- 语法高亮
- 历史记录
- 系统命令执行

**使用的组件:**
- Prompt Toolkit 库
- 命令补全器
- 样式系统
- HTML 渲染器

### 9. asciimatics_wireshark.py - 网络抓包分析工具

```1:44:demo/asciimatics_wireshark.py
from asciimatics.screen import Screen
from asciimatics.scene import Scene
from asciimatics.widgets import (Frame, ListBox, Layout, Label, TextBox, Button, 
                               Widget, Text, PopUpDialog, Divider)
from asciimatics.exceptions import NextScene, StopApplication
from scapy.all import sniff, IP, TCP, UDP, Raw, conf, get_if_list, logging as scapy_logging
from scapy.layers.http import HTTP, HTTPRequest, HTTPResponse
from threading import Thread, Lock
import queue
import time
import re
from collections import defaultdict
import argparse
import netifaces
from asciimatics.event import KeyboardEvent
import psutil
import socket
import threading
from datetime import datetime
import logging
import sys

# 添加日志配置
def setup_logging():
    """配置日志记录"""
    # 创建logger
    logger = logging.getLogger('wireshark_tui')
    logger.setLevel(logging.DEBUG)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.WARNING)
    
    # 创建文件处理器
    log_file = f'wireshark_tui_{datetime.now().strftime("%Y%m%d")}.log'
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    
    # 设置日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
```


**主要功能:**
- 网络数据包捕获
- 数据包分析和过滤
- 实时流量监控
- 日志记录系统

**使用的组件:**
- Asciimatics UI框架
- Scapy 网络库
- 日志系统
- 数据包分析器

### 10. textual_wireshark.py - 基于Textual的抓包工具

```1:644:demo/textual_wireshark.py
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Input, ListView, ListItem, Static, Label
from textual.reactive import reactive
from textual.widget import Widget
from rich.text import Text

import socket
import struct
import time
from datetime import datetime
import logging
import threading
import queue
from typing import Optional, List, Dict, Any
import os
import re
import sys
import select

# 创建logs目录（如果不存在）
if not os.path.exists('logs'):
    os.makedirs('logs')

# 设置日志文件名（使用当前时间）
log_filename = f"logs/capture_{datetime.now().strftime('%Y%m%d')}.log"

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,  # 捕获所有级别的日志
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8')  # 只输出到文件
    ]
)

logger = logging.getLogger(__name__)

# 禁用终端输出
logger.propagate = False

# 确保捕获所有级别的日志
logger.setLevel(logging.DEBUG)
class Packet:
    ...
    def parse(self):
        """解析数据包"""
        try:
            # 直接解析 IP 头
            ip_header = self.data[:20]
            iph = struct.unpack('!BBHHHBBH4s4s', ip_header)
            
            version_ihl = iph[0]
            self.protocol = iph[6]
            self.src_ip = socket.inet_ntoa(iph[8])
            self.dst_ip = socket.inet_ntoa(iph[9])
            
            # 获取 IP 头长度
            ihl = version_ihl & 0xF
            iph_length = ihl * 4
            
            # TCP
            if self.protocol == 6:
                self.protocol = "TCP"
                tcp_header = self.data[iph_length:iph_length+20]
                tcph = struct.unpack('!HHLLBBHHH', tcp_header)
                self.src_port = tcph[0]
                self.dst_port = tcph[1]
                
                # 计算TCP数据偏移
                tcp_offset = (tcph[4] >> 4) * 4
                payload_offset = iph_length + tcp_offset
                payload = self.data[payload_offset:]
                
                # 检查是否是HTTP流量
                if self.src_port == 80 or self.dst_port == 80 or \
                   self.src_port == 8080 or self.dst_port == 8080:
                    self._parse_http(payload)
                else:
                    self.info = f"Seq={tcph[2]} Ack={tcph[3]}"
                
            # UDP
            elif self.protocol == 17:
                self.protocol = "UDP"
                udp_header = self.data[iph_length:iph_length+8]
                udph = struct.unpack('!HHHH', udp_header)
                self.src_port = udph[0]
                self.dst_port = udph[1]
                self.info = f"Len={udph[2]}"
                
            # ICMP
            elif self.protocol == 1:
                self.protocol = "ICMP"
                icmp_header = self.data[iph_length:iph_length+4]
                icmph = struct.unpack('!BBH', icmp_header)
                self.info = f"Type={icmph[0]} Code={icmph[1]}"
    ...
    def get_details(self) -> str:
        """获取详细信息"""
        details = [
            "=== 数据包详情 ===",
            f"时间: {datetime.fromtimestamp(self.timestamp)}",
            f"长度: {self.length} 字节",
            "",
            "=== IP层 ===",
            f"源IP: {self.src_ip}",
            f"目标IP: {self.dst_ip}",
            f"协议: {self.protocol}",
        ]
        
        if self.protocol in ("TCP", "UDP"):
            details.extend([
                "",
                f"=== {self.protocol}层 ===",
                f"源端口: {self.src_port}",
                f"目标端口: {self.dst_port}",
                f"信息: {self.info}"
            ])
            
        # 添加HTTP信息
        if self.protocol == "HTTP" and self.http_info:
            details.extend([
                "",
                "=== HTTP层 ===",
                f"类型: {self.http_info.get('type', 'Unknown')}"
            ])
            
            if self.http_info.get('type') == 'Request':
                details.extend([
                    f"方法: {self.http_info.get('method', '')}",
                    f"路径: {self.http_info.get('path', '')}",
                    f"版本: {self.http_info.get('version', '')}"
                ])
            else:
                details.extend([
                    f"状态码: {self.http_info.get('status_code', '')}",
                    f"状态信息: {self.http_info.get('status_text', '')}",
                    f"内容类型: {self.http_info.get('content_type', 'N/A')}",
                    f"内容长度: {self.http_info.get('content_length', 'N/A')}"
                ])
...
class FilterInput(Input):
    """过滤输入框"""
    def __init__(self):
        super().__init__(placeholder="输入过滤条件 (例如: tcp/udp/http/ip=192.168.1.1/port=80)")
        
    def on_change(self, event):
        """当输入变化时触发过滤"""
        self.parent.apply_filter(self.value)

class FilteredPacketList(ListView):
    """过滤后的数据包列表"""
    def compose(self) -> ComposeResult:
        yield ListItem(Label("等待数据包..."))
        
    def add_packet(self, packet: Packet):
        """添加数据包到列表"""
        self.mount(ListItem(Label(str(packet))))
        # 保持最新的1000个数据包
        if len(self.children) > 1000:
            self.children[0].remove()
class TrafficMonitor(Static):
    """流量监控组件"""
    def __init__(self):
        super().__init__("等待流量数据...")
        self.last_bytes = 0
        self.last_time = time.time()
        self.current_speed = 0
        self.total_bytes = 0
        self.start_time = time.time()
        self.packet_count = 0
        
    def update_traffic(self, total_bytes: int, packet_count: int):
        """更新流量数据"""
        current_time = time.time()
        time_diff = current_time - self.last_time
        
        if time_diff > 0:
            bytes_diff = total_bytes - self.last_bytes
            self.current_speed = bytes_diff / time_diff
            self.last_bytes = total_bytes
            self.last_time = current_time
            self.total_bytes = total_bytes
            self.packet_count = packet_count
            
            # 计算平均速度
            avg_speed = self.total_bytes / (current_time - self.start_time)
            
            # 格式化显示
            current_speed_text = self._format_speed(self.current_speed)
            avg_speed_text = self._format_speed(avg_speed)
            total_bytes_text = self._format_bytes(self.total_bytes)
            
            print(f"流量更新 - 当前速度: {current_speed_text}, 平均速度: {avg_speed_text}, 总流量: {total_bytes_text}")
            
            # 更新显示
            self.update(
                f"当前流量: {current_speed_text}\n"
                f"平均流量: {avg_speed_text}\n"
                f"总流量: {total_bytes_text}\n"
                f"数据包数: {self.packet_count}"
            )
...
class MainContent(Container):
    """主内容区域"""
    def __init__(self):
        super().__init__()
        self.filter_input = FilterInput()
        self.filtered_list = FilteredPacketList()
        self.traffic_monitor = TrafficMonitor()
        self.filter_condition = ""
        
    def compose(self) -> ComposeResult:
        """构建界面"""
        with Horizontal():
            # 左侧部分
            with Vertical():
                yield self.filter_input
                yield self.filtered_list
            
            # 右侧部分
            with Vertical():
                yield self.traffic_monitor
                
    def apply_filter(self, filter_text: str):
        """应用过滤条件"""
        self.filter_condition = filter_text.lower()
        self.refresh_filtered_list()
        
    def refresh_filtered_list(self):
        """刷新过滤后的列表"""
        self.filtered_list.clear()
        
        if hasattr(self, 'capture'):
            for packet in self.capture.packet_list:
                if self._packet_matches_filter(packet):
                    self.filtered_list.add_packet(packet)
                    
    def _packet_matches_filter(self, packet: Packet) -> bool:
        """检查数据包是否匹配过滤条件"""
        if not self.filter_condition:
            return True
            
        filter_parts = self.filter_condition.split('/')
        for part in filter_parts:
            if not part:
                continue
                
            if '=' in part:
                key, value = part.split('=', 1)
                if key == 'ip':
                    if value not in (packet.src_ip, packet.dst_ip):
                        return False
                elif key == 'port':
                    port = int(value)
                    if port not in (packet.src_port, packet.dst_port):
                        return False
            else:
                if part == 'tcp' and packet.protocol != 'TCP':
                    return False
                elif part == 'udp' and packet.protocol != 'UDP':
                    return False
                elif part == 'http' and packet.protocol != 'HTTP':
                    return False
                    
        return True
class PacketDetails(Static):
    """数据包详情组件"""
    def __init__(self):
        super().__init__("选择数据包查看详情", markup=False)
        
    def show_packet(self, packet: Packet):
        """显示数据包详情"""
        self.update(packet.get_details())
class WiresharkApp(App):
    """主应用类"""
    CSS = """
    MainContent {
        height: 70%;
        border: solid green;
    }
    
    Horizontal {
        height: 100%;
    }
    
    Vertical {
        width: 50%;
        height: 100%;
    }
    
    FilterInput {
        dock: top;
        width: 100%;
        height: 3;
        border: solid blue;
    }
    
    FilteredPacketList {
        width: 100%;
        height: 1fr;
        border: solid red;
    }
    
    TrafficMonitor {
        width: 100%;
        height: 100%;
        border: solid yellow;
        content-align: center middle;
    }
    
    PacketDetails {
        height: 30%;
        border: solid blue;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "退出"),
        Binding("c", "clear", "清除"),
    ]
    
    def __init__(self, interface: str):
        super().__init__()
        self.interface = interface
        self.capture = PacketCapture()
        self.main_content = MainContent()
        self.packet_details = PacketDetails()
        
    def compose(self) -> ComposeResult:
        """构建界面"""
        yield Header()
        yield self.main_content
        yield self.packet_details
        yield Footer()
        
    def on_mount(self) -> None:
        """挂载启动捕获"""
        self.capture.start(self.interface)
        self.set_interval(0.1, self.update_display)
```


**主要功能:**
- 网络流量监控
- 数据包过滤
- 流量统计
- 详细数据包信息

**使用的组件:**
- Textual UI框架
- Socket 网络编程
- 反应式状态管理
- 布局系统

### 11. urwid_process_manager.py - 进程管理器

```6:57:demo/urwid_process_manager.py
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
```


**主要功能:**
- 进程列表显示
- 进程详情查看
- 进程控制(结束进程等)
- 系统资源监控

**使用的组件:**
- Urwid UI框架
- 进程管理功能
- 列表视图
- 状态栏系统

### 12. scapy_test.py - 网络数据包分析工具

```1:79:demo/scapy_test.py
from scapy.all import sniff
from scapy.layers.http import HTTP, HTTPRequest, HTTPResponse
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from collections import defaultdict
from urllib.parse import urlparse, parse_qs
from scapy.arch import get_if_list
from scapy.interfaces import NetworkInterface
import netifaces  # 需要安装: pip install netifaces
import platform
import sys

console = Console()
sessions = defaultdict(dict)

def parse_url(host, path):
    """解析 URL，返回 pathname 和 query 参数"""
    if not host or not path:
        return {'pathname': 'N/A', 'query': {}}
    
    full_url = f"http://{host}{path}"
    parsed = urlparse(full_url)
    return {
        'pathname': parsed.path,
        'query': parse_qs(parsed.query)
    }

def format_headers(headers):
    """格式化 HTTP 头部"""
    if not headers:
        return "N/A"
    return "\n".join(f"{k}: {v}" for k, v in headers.items())

def format_body(body):
    """格式化请求/响应体"""
    if not body:
        return "N/A"
    try:
        return body.decode('utf-8')
    except:
        return f"<Binary Data: {len(body)} bytes>"

def print_session(session_key):
    """打印完整的 HTTP 会话信息"""
    session = sessions[session_key]
    if 'request' not in session:
        return
    
    table = Table(show_header=False, box=None)
    table.add_column("Key", style="cyan", width=15)
    table.add_column("Value", style="green")
    
    # 请求信息
    req = session['request']
    url_info = parse_url(req.get('host'), req.get('path'))
    
    table.add_row("请求方法", req.get('method', 'N/A'))
    table.add_row("完整URL", f"http://{req.get('host', '')}{req.get('path', '')}")
    table.add_row("Host", req.get('host', 'N/A'))
    table.add_row("路径", url_info['pathname'])
    table.add_row("查询参数", str(url_info['query']) if url_info['query'] else 'N/A')
    table.add_row("请求头", format_headers(req.get('headers', {})))
    table.add_row("请求体", format_body(req.get('body')))
    
    # 响应信息
    if 'response' in session:
        resp = session['response']
        table.add_row("状态码", resp.get('status', 'N/A'))
        table.add_row("响应头", format_headers(resp.get('headers', {})))
        table.add_row("响应体", format_body(resp.get('body')))
    
    panel = Panel(
        table,
        title=f"HTTP 会话 - {session_key}",
        border_style="blue"
    )
    console.print(panel)
    del sessions[session_key]
```


**主要功能:**
- HTTP 流量分析
- 数据包捕获
- 会话跟踪
- URL 解析

**使用的组件:**
- Scapy 网络库
- Rich 终端美化
- HTTP 协议分析
- 数据格式化

这些示例程序展示了 Python 各种终端库的特性和用法,可以作为开发终端应用的参考。每个示例都专注于特定的功能领域,帮助理解不同库的优势和适用场景。
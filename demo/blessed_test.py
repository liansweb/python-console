from blessed import Terminal
import time
import itertools
import threading
import sys
from typing import Iterator

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

if __name__ == '__main__':
    demo = TerminalDemo()
    demo.run()
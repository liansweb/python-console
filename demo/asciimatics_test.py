from asciimatics.screen import Screen
from asciimatics.scene import Scene
from asciimatics.effects import Cycle, Stars, Print, Matrix
from asciimatics.renderers import FigletText, Rainbow
from asciimatics.exceptions import ResizeScreenError
import sys
import logging

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
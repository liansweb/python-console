from tqdm import tqdm
import time
import random
from typing import Optional

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
import urwid
import json
from datetime import datetime
from enum import Enum

class Priority(Enum):
    LOW = ("💚", "低")
    MEDIUM = ("💛", "中")
    HIGH = ("❤️", "高")

class TaskManager:
    def __init__(self):
        self.tasks = []
        self.current_filter = 'all'  # 'all', 'active', 'completed'
        self.load_tasks()  # 从文件加载任务
        
        self.palette = [
            ('header', 'white,bold', 'dark blue'),
            ('footer', 'white', 'dark blue'),
            ('task', 'black', 'light gray'),
            ('task_done', 'dark gray', 'light gray'),
            ('button', 'black', 'light green'),
            ('button_focus', 'white', 'dark green', 'bold'),
            ('input', 'black', 'light cyan'),
            ('input_focus', 'black', 'yellow'),
            ('error', 'light red', 'dark gray'),
            ('success', 'light green', 'dark gray'),
            ('high_priority', 'dark red', 'light gray'),
            ('medium_priority', 'yellow', 'light gray'),
            ('low_priority', 'dark green', 'light gray'),
        ]
        self.build_interface()

    def build_interface(self):
        # 标题
        header = urwid.AttrMap(
            urwid.Text('\n📝 终端任务管理器 \n', align='center'),
            'header'
        )

        # 任务输入区
        self.task_edit = urwid.Edit('✍️ 新任务: ')
        self.priority_select = self.create_priority_selector()
        input_area = urwid.Columns([
            ('weight', 70, urwid.AttrMap(self.task_edit, 'input', 'input_focus')),
            ('weight', 30, self.priority_select)
        ])

        # 操作按钮
        buttons = [
            ('📝 添加任务', self.add_task),
            ('🗑️ 删除已完成', self.clear_completed),
            ('💾 保存任务', self.save_tasks),
        ]
        button_grid = self.create_button_grid(buttons)

        # 过滤器按钮
        filter_buttons = [
            ('📋 全部', 'all'),
            ('⏳ 进行中', 'active'),
            ('✅ 已完成', 'completed'),
        ]
        filter_grid = self.create_filter_buttons(filter_buttons)

        # 任务列表
        self.task_list = urwid.SimpleFocusListWalker([])
        self.update_task_list()
        list_box = urwid.BoxAdapter(
            urwid.ListBox(self.task_list),
            10
        )

        # 状态栏
        self.status_bar = urwid.Text('🟢 就绪', align='left')
        footer = urwid.AttrMap(self.status_bar, 'footer')

        # 帮助信息
        help_text = urwid.Text([
            '\n快捷键: ',
            ('button', 'Q'), ' 退出 | ',
            ('button', 'D'), ' 删除任务 | ',
            ('button', 'Space'), ' 完成/取消任务\n'
        ], align='center')

        # 主布局
        pile = urwid.Pile([
            ('pack', header),
            ('pack', urwid.Divider('─')),
            ('pack', input_area),
            ('pack', urwid.Divider()),
            ('pack', button_grid),
            ('pack', urwid.Divider()),
            ('pack', filter_grid),
            ('pack', urwid.Divider('─')),
            list_box,
            ('pack', urwid.Divider('─')),
            ('pack', help_text),
            ('pack', footer),
        ])

        # 使用 Padding 包装主布局
        self.main_widget = urwid.Padding(
            pile,
            ('relative', 90),
            min_width=20
        )
        
        # 使用 Filler 处理垂直对齐
        self.main_widget = urwid.Filler(
            self.main_widget,
            'top'
        )

    def create_priority_selector(self):
        """创建优先级选择器"""
        items = [(f"{p.value[0]} {p.value[1]}", p) for p in Priority]
        return urwid.GridFlow(
            [urwid.AttrMap(
                urwid.Button(label, on_press=self.set_priority, user_data=priority),
                'button', 'button_focus'
            ) for label, priority in items],
            cell_width=10, h_sep=1, v_sep=1, align='left'
        )

    def create_button_grid(self, buttons):
        """创建按钮网格"""
        button_widgets = []
        for label, callback in buttons:
            btn = urwid.Button(label)
            btn = urwid.AttrMap(btn, 'button', 'button_focus')
            urwid.connect_signal(btn.original_widget, 'click', callback)
            button_widgets.append(btn)
        return urwid.GridFlow(
            button_widgets, cell_width=20, h_sep=2, v_sep=1, align='center'
        )

    def create_filter_buttons(self, filters):
        """创建过滤器按钮"""
        buttons = []
        for label, filter_type in filters:
            btn = urwid.Button(label, on_press=self.set_filter, user_data=filter_type)
            btn = urwid.AttrMap(btn, 'button', 'button_focus')
            buttons.append(btn)
        return urwid.GridFlow(
            buttons, cell_width=15, h_sep=2, v_sep=1, align='center'
        )

    def create_task_widget(self, task):
        """创建任务项组件"""
        checkbox = urwid.CheckBox(
            f"{task['priority'].value[0]} {task['text']}",
            state=task['completed'],
            on_state_change=self.toggle_task,
            user_data=task
        )
        return urwid.AttrMap(
            checkbox,
            'task_done' if task['completed'] else f"{task['priority'].name.lower()}_priority"
        )

    def add_task(self, button=None):
        """添加新任务"""
        text = self.task_edit.get_edit_text().strip()
        if text:
            task = {
                'text': text,
                'completed': False,
                'priority': getattr(self, 'current_priority', Priority.MEDIUM),
                'created_at': datetime.now().isoformat()
            }
            self.tasks.append(task)
            self.task_edit.set_edit_text('')
            self.update_task_list()
            self.status_bar.set_text('✅ 任务已添加')
        else:
            self.status_bar.set_text('❌ 请输入任务内容')

    def toggle_task(self, checkbox, state, task):
        """切换任务状态"""
        task['completed'] = state
        self.update_task_list()
        self.status_bar.set_text('✅ 任务状态已更新')

    def clear_completed(self, button=None):
        """清除已完成的任务"""
        self.tasks = [task for task in self.tasks if not task['completed']]
        self.update_task_list()
        self.status_bar.set_text('🧹 已清除完成的任务')

    def set_priority(self, button, priority):
        """设置新任务的优先级"""
        self.current_priority = priority
        self.status_bar.set_text(f'📊 已设置优先级: {priority.value[1]}')

    def set_filter(self, button, filter_type):
        """设置任务过滤器"""
        self.current_filter = filter_type
        self.update_task_list()
        self.status_bar.set_text(f'🔍 显示{button.label}任务')

    def update_task_list(self):
        """更新任务列表显示"""
        filtered_tasks = self.filter_tasks()
        del self.task_list[:]
        for task in filtered_tasks:
            self.task_list.append(self.create_task_widget(task))

    def filter_tasks(self):
        """根据当前过滤器过滤任务"""
        if self.current_filter == 'active':
            return [t for t in self.tasks if not t['completed']]
        elif self.current_filter == 'completed':
            return [t for t in self.tasks if t['completed']]
        return self.tasks

    def save_tasks(self, button=None):
        """保存任务到文件"""
        try:
            with open('tasks.json', 'w', encoding='utf-8') as f:
                # 将 Enum 转换为字符串
                tasks_to_save = []
                for task in self.tasks:
                    task_copy = task.copy()
                    task_copy['priority'] = task['priority'].name
                    tasks_to_save.append(task_copy)
                json.dump(tasks_to_save, f, ensure_ascii=False, indent=2)
            self.status_bar.set_text('💾 任务已保存')
        except Exception as e:
            self.status_bar.set_text(f'❌ 保存失败: {str(e)}')

    def load_tasks(self):
        """从文件加载任务"""
        try:
            with open('tasks.json', 'r', encoding='utf-8') as f:
                loaded_tasks = json.load(f)
                for task in loaded_tasks:
                    # 将字符串转换回 Enum
                    task['priority'] = Priority[task['priority']]
                self.tasks = loaded_tasks
        except FileNotFoundError:
            self.tasks = []

    def handle_input(self, key):
        """处理键盘输入"""
        if key in ('q', 'Q'):
            raise urwid.ExitMainLoop()
        elif key == 'D':
            # 删除当前选中的任务
            focus = self.task_list.get_focus()[0]
            if focus:
                task = focus.original_widget.user_data
                self.tasks.remove(task)
                self.update_task_list()
                self.status_bar.set_text('🗑️ 任务已删除')

def main():
    """主程序入口"""
    app = TaskManager()
    loop = urwid.MainLoop(
        app.main_widget,
        app.palette,
        unhandled_input=app.handle_input
    )
    loop.run()

if __name__ == '__main__':
    main() 
import urwid

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
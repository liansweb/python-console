from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, DataTable, Button, Static, Input, RichLog
from textual.binding import Binding
from textual.reactive import reactive
from textual import events, work

from scapy.all import sniff, Raw
from scapy.layers.http import HTTP, HTTPRequest, HTTPResponse
from collections import defaultdict
import re
import operator
import threading
import asyncio

class FilterDSL:
    """HTTP 流量过滤器 DSL 解析器"""
    
    OPERATORS = {
        '=': operator.eq,
        '!=': operator.ne,
        'contains': lambda x, y: y.lower() in x.lower() if x and y else False,
        'startswith': lambda x, y: x.lower().startswith(y.lower()) if x and y else False,
        'endswith': lambda x, y: x.lower().endswith(y.lower()) if x and y else False,
    }
    
    LOGICAL_OPS = {'and', 'or'}
    
    def __init__(self):
        self.filter_expr = ""
        self.compiled_filter = None
    
    def set_filter(self, filter_expr: str):
        """设置过滤表达式"""
        self.filter_expr = filter_expr.strip()
        if not self.filter_expr:
            self.compiled_filter = None
            return
        
        try:
            self.compiled_filter = self._parse_filter(self.filter_expr)
        except Exception as e:
            raise ValueError(f"过滤表达式语法错误: {str(e)}")
    
    def _parse_filter(self, expr):
        """解析过滤表达式"""
        if not expr:
            return lambda _: True
            
        # 分割逻辑运算符
        parts = re.split(r'\s+(and|or)\s+', expr, flags=re.IGNORECASE)
        if len(parts) == 1:
            return self._parse_condition(parts[0])
            
        conditions = []
        operators = []
        for i, part in enumerate(parts):
            if part.lower() in self.LOGICAL_OPS:
                operators.append(part.lower())
            else:
                conditions.append(self._parse_condition(part))
        
        def evaluate(data):
            result = conditions[0](data)
            for i, op in enumerate(operators):
                if op == 'and':
                    result = result and conditions[i + 1](data)
                else:  # or
                    result = result or conditions[i + 1](data)
            return result
            
        return evaluate
    
    def _parse_condition(self, condition):
        """解析单个条件"""
        for op in self.OPERATORS:
            pattern = rf"^([\w-]+)\s*{op}\s*[\"']?([^\"']+)[\"']?$"
            match = re.match(pattern, condition.strip())
            if match:
                field, value = match.groups()
                operator_func = self.OPERATORS[op]
                
                def check(data):
                    if field == 'status' and 'response' in data:
                        actual = str(data['response'].get('status', ''))
                    elif field == 'method' and 'request' in data:
                        actual = data['request'].get('method', '')
                    elif field == 'host' and 'request' in data:
                        actual = data['request'].get('host', '')
                    elif field == 'path' and 'request' in data:
                        actual = data['request'].get('path', '')
                    elif field == 'content-type':
                        actual = ''
                        if 'request' in data and 'headers' in data['request']:
                            actual = data['request']['headers'].get('content-type', '')
                        if not actual and 'response' in data and 'headers' in data['response']:
                            actual = data['response']['headers'].get('content-type', '')
                    else:
                        return False
                    return operator_func(actual, value)
                    
                return check
                
        raise ValueError(f"无效的条件: {condition}")
    
    def match(self, session_data):
        """匹配会话数据"""
        if not self.compiled_filter:
            return True
        
        try:
            result = self.compiled_filter(session_data)
            # 将日志输出传递给主应用
            if hasattr(self, 'app'):
                self.app.log_message(f"过滤表达式: {self.filter_expr}")
                self.app.log_message(f"匹配数据: {session_data}")
                self.app.log_message(f"匹配结果: {result}")
            return result
        except Exception as e:
            if hasattr(self, 'app'):
                self.app.log_message(f"过滤匹配错误: {str(e)}", "error")
            return False

class FilterPanel(Container):
    """过滤器设置面板"""
    def compose(self) -> ComposeResult:
        yield Vertical(
            Static("[bold]HTTP 流量过滤器[/bold]", classes="title"),
            Static("支持的语法示例:", classes="help"),
            Static("method = 'GET' and status = 200", classes="help"),
            Static("host contains 'example.com'", classes="help"),
            Static("path startswith '/api' and content-type contains 'json'", classes="help"),
            Input(placeholder="输入过滤表达式", id="filter_expr"),
            Horizontal(
                Button("应用", variant="primary", id="apply_filter"),
                Button("清除", variant="error", id="clear_filter"),
                classes="button-row"
            ),
            classes="filter-panel"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "apply_filter":
            self.apply_filter()
        elif event.button.id == "clear_filter":
            self.clear_filter()
            
    def apply_filter(self):
        filter_expr = self.query_one("#filter_expr").value
        try:
            self.app.http_session.filter.set_filter(filter_expr)
            self.app.notify("过滤器已应用", severity="information")
        except ValueError as e:
            self.app.notify(str(e), severity="error")
                
    def clear_filter(self):
        self.query_one("#filter_expr").value = ""
        self.app.http_session.filter.set_filter("")
        self.app.notify("过滤器已清除", severity="information")

class HttpSession:
    """HTTP 会话数据模型"""
    def __init__(self, app):
        self.sessions = defaultdict(dict)
        self.filter = FilterDSL()
        self.filter.app = app
        self.app = app
        
    def add_request(self, session_key, request_data):
        self.sessions[session_key]['request'] = request_data
        match_result = self.filter.match(self.sessions[session_key])
        print(f"请求过滤结果: {match_result}, 会话: {session_key}")  # 添加调试日志
        return match_result
        
    def add_response(self, session_key, response_data):
        if session_key in self.sessions:
            self.sessions[session_key]['response'] = response_data
            match_result = self.filter.match(self.sessions[session_key])
            print(f"响应过滤结果: {match_result}, 会话: {session_key}")  # 添加调试日志
            if match_result:
                return self.sessions[session_key]
        return None

class SessionTable(DataTable):
    """HTTP 会话列表"""
    def __init__(self):
        super().__init__()
        self.add_columns(
            "会话ID", "方法", "主机", "路径", "状态码"
        )
        
    def add_session(self, session_key, session_data):
        request = session_data.get('request', {})
        response = session_data.get('response', {})
        self.add_row(
            session_key,
            request.get('method', 'N/A'),
            request.get('host', 'N/A'),
            request.get('path', 'N/A'),
            response.get('status', 'N/A'),
            key=session_key  # 添加key以便后续更新
        )
        # 自动滚动到最新的行
        self.scroll_to_row(len(self.rows) - 1)

    def on_data_table_row_selected(self, event):
        """处理行选择事件"""
        session_key = event.row_key.value
        if session_key:
            session_data = self.app.http_session.sessions.get(session_key)
            if session_data:
                detail = self.app.query_one(SessionDetail)
                detail.session_data = session_data

class SessionDetail(Static):
    """HTTP 会话详情"""
    session_data = reactive(None)
    
    def watch_session_data(self, value):
        if value:
            self.update(self.format_session(value))
            
    def format_session(self, session):
        request = session.get('request', {})
        response = session.get('response', {})
        
        details = []
        details.append("[bold]请求信息[/bold]")
        details.append(f"方法: {request.get('method', 'N/A')}")
        details.append(f"URL: http://{request.get('host', '')}{request.get('path', '')}")
        details.append(f"请求头: {self.format_headers(request.get('headers', {}))}")
        details.append(f"请求体: {self.format_body(request.get('body'))}")
        
        if response:
            details.append("\n[bold]响应信息[/bold]")
            details.append(f"状态码: {response.get('status', 'N/A')}")
            details.append(f"响应头: {self.format_headers(response.get('headers', {}))}")
            details.append(f"响应体: {self.format_body(response.get('body'))}")
            
        return "\n".join(details)
        
    def format_headers(self, headers):
        if not headers:
            return "N/A"
        return "\n".join(f"  {k}: {v}" for k, v in headers.items())
        
    def format_body(self, body):
        if not body:
            return "N/A"
        try:
            return body.decode('utf-8')
        except:
            return f"<Binary Data: {len(body)} bytes>"

class LogPanel(Container):
    """日志展示面板"""
    def compose(self) -> ComposeResult:
        yield Static("[bold]运行日志[/bold]", classes="title")
        yield RichLog(highlight=True, markup=True, id="log_view")
        
    def log(self, message: str, severity: str = "information"):
        """添加日志"""
        log_view = self.query_one("#log_view")
        # 根据不同的严重程度使用不同的颜色
        color_map = {
            "information": "blue",
            "warning": "yellow",
            "error": "red",
            "success": "green"
        }
        color = color_map.get(severity, "white")
        log_view.write(f"[{color}]{message}[/]\n")

class HttpSnifferApp(App):
    """HTTP 抓包分析工具"""
    CSS = """
    Screen {
        layout: horizontal;  /* 水平布局 */
        padding: 1;
    }

    /* 左侧部分 - 占30% */
    #left-panel {
        width: 30%;
        height: 100%;
        margin-right: 1;
    }

    /* 右侧部分 - 占60% */
    #right-panel {
        width: 60%;
        height: 100%;
        margin-left: 1;
    }

    FilterPanel {
        height: 30%;
        border: solid $accent;
        background: $surface;
        margin-bottom: 1;
    }

    SessionTable { 
        height: 30%;
        border: solid $accent;
        margin-bottom: 1;
    }

    SessionDetail { 
        height: 40%;
        border: solid $accent;
        padding: 1;
    }

    LogPanel {
        height: 100%;
        border: solid $accent;
        background: $surface;
    }

    /* 其他样式保持不变 */
    .title { 
        text-align: center; 
        padding: 1;
        background: $accent;
        color: $text;
    }
    
    .help { 
        color: $text-muted; 
        padding-left: 1; 
        margin: 0 1;
    }
    
    FilterPanel Input {
        margin: 1 1;
        border: solid $accent;
        min-height: 3;
    }
    
    .button-row {
        height: auto;
        align-horizontal: center;
        margin: 1;
    }
    
    .button-row Button {
        margin: 0 1;
        min-width: 10;
    }
    
    #log_view {
        height: 100%;
        border: none;
        padding: 1;
        background: $surface;
        color: $text;
        overflow-y: scroll;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "退出"),
        Binding("c", "clear", "清除"),
    ]
    
    def __init__(self):
        super().__init__()
        self.http_session = HttpSession(self)
        self.sniffer_thread = None
        
    def compose(self) -> ComposeResult:
        """重新组织布局结构"""
        yield Header()
        
        # 左侧面板
        with Container(id="left-panel"):
            yield FilterPanel()
            yield SessionTable()
            yield SessionDetail()
        
        # 右侧面板
        with Container(id="right-panel"):
            yield LogPanel()
            
        yield Footer()
        
    def on_mount(self) -> None:
        """应用启动时的处理"""
        self.log_message("应用启动", "information")
        self.start_sniffing()
        
    def on_unmount(self) -> None:
        """应用关闭时的处理"""
        self.log_message("应用关闭", "information")
        if self.sniffer_thread and self.sniffer_thread.is_alive():
            self.sniffer_thread.join()
            
    def log_message(self, message: str, severity: str = "information"):
        """写入日志"""
        log_panel = self.query_one(LogPanel)
        log_panel.log(message, severity)

    @work(thread=True)
    def start_sniffing(self):
        """启动抓包线程"""
        self.log_message("开始抓包...", "information")
        
        def packet_handler(packet):
            # 添加基础包捕获日志
            self.call_from_thread(self.log_message, "捕获到数据包", "information")
            
            if HTTP not in packet:
                return
                
            try:
                if HTTPRequest in packet:
                    self.call_from_thread(self.log_message, "捕获到HTTP请求")
                    request = self.parse_http_request(packet)
                    if request:
                        session_key = f"{request['host']}:{request['path']}"
                        self.call_from_thread(self.log_message, f"处理请求: {session_key}")
                        match_result = self.http_session.add_request(session_key, request)
                        self.call_from_thread(
                            self.log_message, 
                            f"请求匹配结果: {match_result} (会话: {session_key})"
                        )
                        if match_result:
                            self.call_from_thread(self.update_session_table, session_key)
                        
                elif HTTPResponse in packet:
                    self.call_from_thread(self.log_message, "捕获到HTTP响应")
                    response = self.parse_http_response(packet)
                    if response:
                        session_key = self.find_session_key(packet)
                        if session_key:
                            self.call_from_thread(self.log_message, f"处理响应: {session_key}")
                            session = self.http_session.add_response(session_key, response)
                            self.call_from_thread(
                                self.log_message,
                                f"响应匹配结果: {bool(session)} (会话: {session_key})"
                            )
                            if session:
                                self.call_from_thread(self.update_session_table, session_key)
            except Exception as e:
                self.call_from_thread(
                    self.log_message, 
                    f"错误: {str(e)}", 
                    "error"
                )

        try:
            # 添加具体的抓包参数
            self.log_message("启动抓包监听...", "information")
            sniff(prn=packet_handler, store=0, filter="tcp port 80")
        except Exception as e:
            self.log_message(f"抓包错误: {str(e)}", "error")

    def parse_http_request(self, packet):
        """解析HTTP请求"""
        try:
            http_layer = packet[HTTPRequest]
            return {
                'method': http_layer.Method.decode(),
                'host': http_layer.Host.decode() if hasattr(http_layer, 'Host') else '',
                'path': http_layer.Path.decode(),
                'headers': self.parse_headers(http_layer),
                'body': bytes(packet[Raw]) if Raw in packet else b''
            }
        except Exception as e:
            print(f"解析HTTP请求失败: {e}")
            return None

    def parse_http_response(self, packet):
        """解析HTTP响应包"""
        try:
            http_layer = packet[HTTPResponse]
            return {
                'status': str(http_layer.Status_Code),
                'headers': self.parse_headers(http_layer),
                'body': bytes(packet[Raw]) if Raw in packet else b''
            }
        except Exception as e:
            print(f"解析HTTP响应失败: {e}")
            return None

    def parse_headers(self, http_layer):
        """解析HTTP头部"""
        headers = {}
        for field in http_layer.fields_desc:
            if field.name.startswith('Unknown_'):
                continue
            value = getattr(http_layer, field.name)
            if value:
                try:
                    headers[field.name] = value.decode()
                except:
                    headers[field.name] = str(value)
        return headers

    def find_session_key(self, packet):
        """根据IP和端口找到对应的会话"""
        try:
            if packet.haslayer('IP'):
                dst_ip = packet['IP'].dst
                for session_key, session in self.http_session.sessions.items():
                    if 'request' in session and session['request'].get('host') in dst_ip:
                        return session_key
        except Exception as e:
            self.log.error(f"查找会话键错误: {str(e)}")
        return None

    def update_session_table(self, session_key):
        """更新会话表格"""
        try:
            session_data = self.http_session.sessions.get(session_key)
            if session_data:
                table = self.query_one(SessionTable)
                existing_row = None
                
                # 查找现有行
                for row_key, row in enumerate(table.rows):
                    if row[0] == session_key:
                        existing_row = row_key
                        break
                
                # 如果行存在则更新，否则添加新行
                if existing_row is not None:
                    request = session_data.get('request', {})
                    response = session_data.get('response', {})
                    table.update_cell(existing_row, "方法", request.get('method', 'N/A'))
                    table.update_cell(existing_row, "主机", request.get('host', 'N/A'))
                    table.update_cell(existing_row, "路径", request.get('path', 'N/A'))
                    table.update_cell(existing_row, "状态码", response.get('status', 'N/A'))
                    self.log_message(f"更新会话: {session_key}")
                else:
                    table.add_session(session_key, session_data)
                    self.log_message(f"添加新会话: {session_key}")
                
                detail = self.query_one(SessionDetail)
                detail.session_data = session_data
        except Exception as e:
            self.log_message(f"更新会话表格错误: {str(e)}", "error")

if __name__ == "__main__":
    app = HttpSnifferApp()
    app.run() 
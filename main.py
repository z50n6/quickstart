import sys
import os
import json
import subprocess
import threading
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QStatusBar, QProgressBar, QMessageBox, QScrollArea, QLineEdit, QSizePolicy, QSpacerItem, QFileDialog, QComboBox, QTextEdit, QDialogButtonBox, QDialog, QTreeWidget, QTreeWidgetItem
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtCore import QUrl

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '../config.json')

# 工具数据结构
class Tool:
    def __init__(self, data):
        self.name = data.get('name', '')
        self.path = data.get('path', '')
        self.tool_type = data.get('tool_type', '')
        self.description = data.get('description', '')
        self.icon_path = data.get('icon_path', None)
        self.args = data.get('args', '')
        self.category = data.get('category', '')
        self.launch_count = data.get('launch_count', 0)
        self.last_launch = data.get('last_launch', '')
        self.tags = []
        # 自动提取标签（如有）
        if 'category' in data and data['category']:
            self.tags.append(data['category'])
        # 可扩展更多标签字段

# 工具卡片
class ToolCard(QWidget):
    def __init__(self, tool, launch_callback=None, parent=None, edit_callback=None, open_folder_callback=None, open_cmd_callback=None, copy_path_callback=None, copy_info_callback=None, delete_callback=None):
        super().__init__(parent)
        self.tool = tool
        self.launch_callback = launch_callback
        self.edit_callback = edit_callback
        self.open_folder_callback = open_folder_callback
        self.open_cmd_callback = open_cmd_callback
        self.copy_path_callback = copy_path_callback
        self.copy_info_callback = copy_info_callback
        self.delete_callback = delete_callback
        self.setMinimumHeight(90)
        self.setStyleSheet("""
        QWidget[isCard="true"] {
            background: white;
            border: 1px solid #e9ecef;
            border-radius: 10px;
        }
        QWidget[isCard="true"]:hover {
            border: 1px solid #43e97b;
            background: #f8f9fa;
        }
        """)
        self.setProperty("isCard", True)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(15)
        # 图标
        icon_label = QLabel()
        icon_label.setFixedSize(48, 48)
        icon_label.setAlignment(Qt.AlignCenter)
        if tool.icon_path and os.path.exists(tool.icon_path):
            pixmap = QPixmap(tool.icon_path)
            icon_label.setPixmap(pixmap.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            icon_label.setText("🚀")
        layout.addWidget(icon_label)
        # 信息
        info_layout = QVBoxLayout()
        name_label = QLabel(tool.name)
        name_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #212529;")
        info_layout.addWidget(name_label)
        desc_label = QLabel(f"类型: {tool.tool_type} | 启动: {tool.launch_count} 次")
        desc_label.setStyleSheet("font-size: 12px; color: #6c757d;")
        info_layout.addWidget(desc_label)
        # 分类标签
        tag_layout = QHBoxLayout()
        for tag in tool.tags:
            tag_label = QLabel(f"{tag}")
            tag_label.setStyleSheet("background: #e3f2fd; color: #1976d2; border-radius: 8px; padding: 2px 8px; font-size: 11px; font-weight: bold; margin-top: 2px;")
            tag_layout.addWidget(tag_label)
        tag_layout.addStretch()
        info_layout.addLayout(tag_layout)
        layout.addLayout(info_layout, 1)
        # 启动按钮
        launch_btn = QPushButton("🚀 启动")
        launch_btn.setFixedSize(90, 36)
        launch_btn.setCursor(Qt.PointingHandCursor)
        launch_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #667eea, stop:1 #764ba2);
                color: white; border: none; border-radius: 18px; font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #764ba2, stop:1 #667eea); }
            QPushButton:pressed { background: #5a67d8; }
        """)
        launch_btn.clicked.connect(lambda: self.launch_tool())
        layout.addWidget(launch_btn)
        # 右键菜单
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def launch_tool(self):
        if self.launch_callback:
            self.launch_callback(self.tool)

    def show_context_menu(self, pos):
        from PyQt5.QtWidgets import QMenu, QAction
        menu = QMenu(self)
        # 启动
        action_launch = QAction("🚀 启动工具", self)
        action_launch.triggered.connect(lambda: self.launch_tool())
        menu.addAction(action_launch)
        # 编辑
        if self.edit_callback:
            action_edit = QAction("✏️ 编辑工具", self)
            action_edit.triggered.connect(lambda: self.edit_callback(self.tool))
            menu.addAction(action_edit)
        # 打开所在文件夹
        if self.open_folder_callback:
            action_folder = QAction("📁 打开所在文件夹", self)
            action_folder.triggered.connect(lambda: self.open_folder_callback(self.tool))
            menu.addAction(action_folder)
        # 打开命令行
        if self.open_cmd_callback:
            action_cmd = QAction("💻 打开命令行", self)
            action_cmd.triggered.connect(lambda: self.open_cmd_callback(self.tool))
            menu.addAction(action_cmd)
        menu.addSeparator()
        # 复制路径
        if self.copy_path_callback:
            action_copy_path = QAction("📋 复制路径", self)
            action_copy_path.triggered.connect(lambda: self.copy_path_callback(self.tool))
            menu.addAction(action_copy_path)
        # 复制工具信息
        if self.copy_info_callback:
            action_copy_info = QAction("📄 复制工具信息", self)
            action_copy_info.triggered.connect(lambda: self.copy_info_callback(self.tool))
            menu.addAction(action_copy_info)
        menu.addSeparator()
        # 删除
        if self.delete_callback:
            action_delete = QAction("🗑️ 删除工具", self)
            action_delete.triggered.connect(lambda: self.delete_callback(self.tool))
            menu.addAction(action_delete)
        menu.exec(self.mapToGlobal(pos))

# pip依赖安装线程
class PipInstallerWorker(QObject):
    installationStarted = pyqtSignal(str)
    installationProgress = pyqtSignal(str, str)
    installationFinished = pyqtSignal(str, bool, str)
    def install(self, tool, target):
        self.installationStarted.emit(tool.name)
        try:
            if target == 'requirements':
                req_file = os.path.join(os.path.dirname(tool.path), 'requirements.txt')
                cmd = [sys.executable, '-m', 'pip', 'install', '-r', req_file]
                self.installationProgress.emit(tool.name, f"正在从 requirements.txt 安装依赖...")
            else:
                cmd = [sys.executable, '-m', 'pip', 'install', target]
                self.installationProgress.emit(tool.name, f"正在安装模块: {target}...")
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace')
            for line in iter(process.stdout.readline, ''):
                self.installationProgress.emit(tool.name, line.strip())
            process.stdout.close()
            return_code = process.wait()
            if return_code == 0:
                self.installationProgress.emit(tool.name, "依赖安装成功!")
                self.installationFinished.emit(tool.name, True, "")
            else:
                error_msg = f"Pip 安装失败，返回码: {return_code}"
                self.installationProgress.emit(tool.name, error_msg)
                self.installationFinished.emit(tool.name, False, error_msg)
        except Exception as e:
            error_msg = f"安装过程中发生错误: {e}"
            self.installationProgress.emit(tool.name, error_msg)
            self.installationFinished.emit(tool.name, False, error_msg)

# 工具启动线程
class ToolLauncherWorker(QObject):
    toolLaunched = pyqtSignal(str, bool, str)
    installationRequired = pyqtSignal(object, str)
    def launch_tool(self, tool):
        try:
            if tool.tool_type == "python":
                tool_dir = os.path.dirname(tool.path)
                req_file = os.path.join(tool_dir, 'requirements.txt')
                if os.path.exists(req_file):
                    self.installationRequired.emit(tool, 'requirements')
                    return
                cmd = [sys.executable, tool.path]
                if tool.args:
                    cmd.extend(tool.args.split())
                process = subprocess.run(cmd, cwd=tool_dir, capture_output=True, text=True, encoding='utf-8', errors='replace')
                if process.returncode != 0:
                    stderr = process.stderr
                    if "ModuleNotFoundError" in stderr:
                        import re
                        match = re.search(r"ModuleNotFoundError: No module named '([\w\.]+)'", stderr)
                        if match:
                            module_name = match.group(1)
                            self.installationRequired.emit(tool, module_name)
                            return
                    self.toolLaunched.emit(tool.name, False, stderr or process.stdout)
                    return
            elif tool.tool_type in ["exe", "vbs", "batch", "java8_gui", "java11_gui", "java8", "java11"]:
                subprocess.Popen([tool.path] + tool.args.split(), shell=True)
            else:
                self.toolLaunched.emit(tool.name, False, "暂不支持该类型")
                return
            self.toolLaunched.emit(tool.name, True, "")
        except Exception as e:
            self.toolLaunched.emit(tool.name, False, str(e))

# 主窗口
class QuickStartMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('quickstart - 极简安全工具')
        self.setGeometry(500, 500, 1100, 800)
        self.init_ui()
        self.init_workers()
        self.tools = self.load_tools()
        self.filtered_tools = self.tools
        self.build_category_tree()
        self.show_tools()
    def init_ui(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_label = QLabel("就绪")
        self.status_label.setMaximumWidth(16777215)  # 允许最大宽度
        self.status_label.setMinimumWidth(0)
        self.status_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.status_label.setStyleSheet("QLabel { qproperty-alignment: AlignVCenter | AlignLeft; }")
        self.status_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.status_label.setWordWrap(False)
        self.status_label.setToolTip("状态栏信息过长时可悬停查看全部")
        self.status_label.setTextFormat(Qt.PlainText)
        self.status_bar.addWidget(self.status_label, 1)  # 拉伸因子为1，自动填满
        self.install_progress_bar = QProgressBar()
        self.install_progress_bar.setVisible(False)
        self.install_progress_bar.setFixedWidth(200)
        self.status_bar.addPermanentWidget(self.install_progress_bar)
        # 顶部搜索框
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索工具名称、描述或分类...")
        self.search_input.setFixedHeight(36)
        self.search_input.setStyleSheet("font-size: 16px; border-radius: 18px; padding-left: 18px; background: #fff; border: 1.5px solid #e9ecef; margin-right: 8px;")
        self.search_input.textChanged.connect(self.on_search_text_changed)
        # 搜索统计标签
        self.search_stats = QLabel()
        self.search_stats.setStyleSheet("font-size: 15px; color: #888; padding-left: 12px;")
        # 放大镜图标
        self.search_icon = QLabel("🔍")
        self.search_icon.setStyleSheet("font-size: 18px; padding-right: 8px;")
        # 添加工具按钮
        self.add_tool_btn = QPushButton("➕ 添加工具")
        self.add_tool_btn.setFixedHeight(36)
        self.add_tool_btn.setStyleSheet("font-size: 16px; border-radius: 18px; background: #43e97b; color: #fff; padding: 0 18px; margin-left: 12px;")
        self.add_tool_btn.setMinimumWidth(120)
        self.add_tool_btn.clicked.connect(self.add_tool)
        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)
        top_layout.setContentsMargins(16, 12, 16, 0)
        top_layout.setSpacing(0)
        top_layout.addWidget(self.search_icon)
        top_layout.addWidget(self.search_input)
        top_layout.addWidget(self.search_stats)
        top_layout.addWidget(self.add_tool_btn)
        top_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        # 分类大纲
        self.category_tree = QTreeWidget()
        self.category_tree.setHeaderHidden(True)
        self.category_tree.setFixedWidth(220)
        self.category_tree.itemClicked.connect(self.on_category_clicked)
        # self.build_category_tree()  # 移除这里的调用
        # 工具区
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.container = QWidget()
        self.vbox = QVBoxLayout(self.container)
        self.vbox.setAlignment(Qt.AlignTop)
        self.scroll.setWidget(self.container)
        # 主布局
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        # 左侧：分类树
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        left_layout.addWidget(self.category_tree)
        left_widget = QWidget()
        left_widget.setLayout(left_layout)
        main_layout.addWidget(left_widget)
        # 右侧：搜索+工具区
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        right_layout.addWidget(top_widget)
        right_layout.addWidget(self.scroll)
        right_widget = QWidget()
        right_widget.setLayout(right_layout)
        main_layout.addWidget(right_widget, 1)
        self.setCentralWidget(main_widget)
        self.setMinimumSize(1100, 800)
        self.setMaximumSize(16777215, 16777215)
    def add_tool(self):
        dialog = ToolEditDialog(self, None, self.get_all_categories())
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            new_tool = Tool({
                "name": data["name"],
                "tool_type": data["tool_type"],
                "path": data["path"],
                "icon_path": data["icon_path"],
                "category": data["category"],
                "args": data["args"],
                "description": data["description"],
                "launch_count": 0,
                "last_launch": ""
            })
            self.tools.append(new_tool)
            self.save_tools()
            self.build_category_tree()
            self.show_tools()
    def init_workers(self):
        self.pip_thread = QThread()
        self.pip_worker = PipInstallerWorker()
        self.pip_worker.moveToThread(self.pip_thread)
        self.pip_thread.start()
        self.launch_thread = QThread()
        self.launch_worker = ToolLauncherWorker()
        self.launch_worker.moveToThread(self.launch_thread)
        self.launch_thread.start()
        self.pip_worker.installationStarted.connect(self.handle_installation_started)
        self.pip_worker.installationProgress.connect(self.handle_installation_progress)
        self.pip_worker.installationFinished.connect(self.handle_installation_finished)
        self.launch_worker.toolLaunched.connect(self.handle_tool_launched)
        self.launch_worker.installationRequired.connect(self.handle_installation_required)
    def load_tools(self):
        # 从 config.json 读取工具列表
        if not os.path.exists(CONFIG_PATH):
            QMessageBox.critical(self, "错误", f"未找到配置文件: {CONFIG_PATH}")
            return []
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return [Tool(item) for item in data.get('tools', [])]
    def show_tools(self):
        # 清空
        for i in reversed(range(self.vbox.count())):
            item = self.vbox.itemAt(i)
            widget = item.widget() if item else None
            if widget:
                widget.setParent(None)
            else:
                self.vbox.removeItem(item)
        # 启动次数降序排序
        sorted_tools = sorted(self.filtered_tools, key=lambda t: t.launch_count, reverse=True)
        card_count = 0
        for tool in sorted_tools:
            card = ToolCard(tool, launch_callback=self.launch_tool,
                            edit_callback=self.edit_tool,
                            open_folder_callback=self.open_folder,
                            open_cmd_callback=self.open_cmd,
                            copy_path_callback=self.copy_path,
                            copy_info_callback=self.copy_info,
                            delete_callback=self.delete_tool)
            self.vbox.addWidget(card)
            card_count += 1
        if card_count == 0:
            self.vbox.addStretch()
        total = len(self.tools)
        found = len(self.filtered_tools)
        self.search_stats.setText(f"找到 {found} 个工具(共 {total} 个)")
    def launch_tool(self, tool, dependency_check=True):
        def run():
            import shutil
            import os, sys, subprocess
            from PyQt5.QtGui import QDesktopServices
            from PyQt5.QtCore import QUrl
            def get_java_path(ver):
                env = os.environ.get('JAVA8_HOME' if ver==8 else 'JAVA11_HOME')
                if env and os.path.isfile(os.path.join(env, 'bin', 'java.exe')):
                    return os.path.join(env, 'bin', 'java.exe')
                config_path = None
                try:
                    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        config_path = data.get('java8_path' if ver==8 else 'java11_path', None)
                except Exception:
                    pass
                if config_path and os.path.isfile(config_path):
                    return config_path
                return shutil.which('java')
            try:
                if tool.tool_type == "folder":
                    if os.path.isdir(tool.path):
                        QDesktopServices.openUrl(QUrl.fromLocalFile(tool.path))
                        self.set_status(f"已打开文件夹: {tool.path}")
                    else:
                        self.set_status(f"❌ 文件夹不存在: {tool.path}")
                        QMessageBox.critical(self, "错误", f"文件夹不存在: {tool.path}")
                    return
                if tool.tool_type == "batch":
                    bat_path = os.path.abspath(tool.path)
                    cmd = ["cmd.exe", "/k", bat_path]
                    if tool.args:
                        cmd.extend(tool.args.split())
                    tool_dir = os.path.dirname(bat_path) or None
                    CREATE_NEW_CONSOLE = 0x00000010
                    subprocess.Popen(cmd, cwd=tool_dir, creationflags=CREATE_NEW_CONSOLE)
                    self.set_status(f"已启动批处理: {tool.name}")
                    return
                if tool.tool_type in ["java8_gui", "java8"]:
                    java_path = get_java_path(8)
                    if not java_path:
                        self.set_status("❌ 未找到Java8环境")
                        QMessageBox.critical(self, "错误", "未找到Java8环境，请配置JAVA8_HOME或config.json中的java8_path")
                        return
                    cmd = [java_path, "-jar", tool.path] if tool.tool_type == "java8_gui" else [java_path]
                    if tool.args:
                        cmd.extend(tool.args.split())
                    subprocess.Popen(cmd, cwd=os.path.dirname(tool.path))
                    return
                if tool.tool_type in ["java11_gui", "java11"]:
                    java_path = get_java_path(11)
                    if not java_path:
                        self.set_status("❌ 未找到Java11环境")
                        QMessageBox.critical(self, "错误", "未找到Java11环境，请配置JAVA11_HOME或config.json中的java11_path")
                        return
                    cmd = [java_path, "-jar", tool.path] if tool.tool_type == "java11_gui" else [java_path]
                    if tool.args:
                        cmd.extend(tool.args.split())
                    subprocess.Popen(cmd, cwd=os.path.dirname(tool.path))
                    return
                if tool.tool_type == "python":
                    tool_dir = os.path.dirname(tool.path)
                    req_file = os.path.join(tool_dir, 'requirements.txt')
                    if dependency_check and os.path.exists(req_file):
                        # 先安装依赖
                        self.set_status(f"[{tool.name}] 正在从 requirements.txt 安装依赖...")
                        self.handle_installation_required(tool, 'requirements')
                        return
                    # 依赖已满足，直接启动
                    cmd = [sys.executable, tool.path]
                    if tool.args:
                        cmd.extend(tool.args.split())
                    subprocess.Popen(cmd, cwd=tool_dir)
                    self.set_status(f"已启动: {tool.name}")
                    return
                if tool.tool_type == "vbs":
                    vbs_path = os.path.abspath(tool.path)
                    cmd = ["wscript.exe", vbs_path]
                    if tool.args:
                        cmd.extend(tool.args.split())
                    tool_dir = os.path.dirname(vbs_path) or None
                    subprocess.Popen(cmd, cwd=tool_dir)
                    self.set_status(f"已启动: {tool.name}")
                    return
                if tool.tool_type == "url":
                    QDesktopServices.openUrl(QUrl(tool.path))
                    self.set_status(f"已打开网址: {tool.path}")
                    return
                # 其它类型默认直接启动
                exe_path = tool.path
                if not os.path.exists(exe_path):
                    self.set_status(f"❌ 文件不存在: {exe_path}")
                    QMessageBox.critical(self, "错误", f"文件不存在: {exe_path}")
                    return
                cmd = [exe_path]
                if tool.args:
                    cmd.extend(tool.args.split())
                subprocess.Popen(cmd, cwd=os.path.dirname(exe_path))
                self.set_status(f"已启动: {tool.name}")
            except Exception as e:
                self.set_status(f"❌ 启动失败: {e}")
                QMessageBox.critical(self, "启动失败", f"启动 {tool.name} 失败: {e}")
        threading.Thread(target=run).start()

    def handle_installation_required(self, tool, target):
        threading.Thread(target=lambda: self.pip_worker.install(tool, target)).start()

    def handle_installation_started(self, tool_name):
        self.install_progress_bar.setVisible(True)
        self.install_progress_bar.setRange(0, 0)
        self.set_status(f"为 {tool_name} 开始安装依赖...")

    def handle_installation_progress(self, tool_name, message):
        self.set_status(f"[{tool_name}] {message}")

    def handle_installation_finished(self, tool_name, success, error_msg):
        self.install_progress_bar.setVisible(False)
        self.install_progress_bar.setRange(0, 100)
        tool = next((t for t in self.tools if t.name == tool_name), None)
        if success:
            self.set_status(f"✅ {tool_name} 依赖安装成功，正在重新启动...")
            if tool:
                self.launch_tool(tool, dependency_check=False)
        else:
            self.set_status(f"❌ {tool_name} 依赖安装失败: {error_msg}")
            QMessageBox.critical(self, "安装失败", f"为 {tool_name} 安装依赖失败: \n{error_msg}")

    def handle_tool_launched(self, tool_name, success, result):
        if success:
            self.set_status(f"✅ 已启动: {tool_name}")
        else:
            self.set_status(f"❌ 启动失败: {tool_name} - {result}")
            QMessageBox.critical(self, "启动失败", f"启动 {tool_name} 失败: {result}")

    def on_search_text_changed(self, text):
        text = text.strip().lower()
        if not text:
            self.filtered_tools = self.tools
        else:
            self.filtered_tools = [t for t in self.tools if text in t.name.lower() or text in t.description.lower() or text in t.category.lower()]
        self.show_tools()

    def edit_tool(self, tool):
        dialog = ToolEditDialog(self, tool, self.get_all_categories())
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            tool.name = data["name"]
            tool.tool_type = data["tool_type"]
            tool.path = data["path"]
            tool.icon_path = data["icon_path"]
            tool.category = data["category"]
            tool.args = data["args"]
            tool.description = data["description"]
            self.save_tools()
            self.show_tools()

    def open_folder(self, tool):
        import subprocess, os
        folder = os.path.dirname(tool.path)
        if os.path.exists(folder):
            if sys.platform.startswith('win'):
                os.startfile(folder)
            elif sys.platform.startswith('darwin'):
                subprocess.Popen(['open', folder])
            else:
                subprocess.Popen(['xdg-open', folder])

    def open_cmd(self, tool):
        import subprocess, os, sys
        folder = os.path.dirname(tool.path)
        if os.path.exists(folder):
            if sys.platform.startswith('win'):
                CREATE_NEW_CONSOLE = 0x00000010
                terminal_options = [
                    {"cmd": ["wt.exe", "-d", folder], "args": {}, "name": "Windows Terminal"},
                    {"cmd": ["pwsh.exe", "-NoExit"], "args": {"cwd": folder}, "name": "PowerShell Core"},
                    {"cmd": ["powershell.exe", "-NoExit"], "args": {"cwd": folder}, "name": "Windows PowerShell"},
                    {"cmd": ["cmd.exe"], "args": {"cwd": folder}, "name": "Command Prompt"}
                ]
                for option in terminal_options:
                    try:
                        subprocess.Popen(option["cmd"], creationflags=CREATE_NEW_CONSOLE, **option["args"])
                        self.set_status(f"✅ 已用 {option['name']} 打开命令行: {folder}")
                        return
                    except FileNotFoundError:
                        continue
                    except Exception:
                        continue
                QMessageBox.critical(self, "错误", "无法打开任何终端。请检查您的系统配置。")
            elif sys.platform.startswith('darwin'):
                subprocess.Popen(['open', '-a', 'Terminal', folder])
            else:
                try:
                    subprocess.Popen(['gnome-terminal', '--working-directory', folder])
                except FileNotFoundError:
                    subprocess.Popen(['x-terminal-emulator', '--working-directory', folder])

    def copy_path(self, tool):
        QApplication.clipboard().setText(tool.path)
        self.set_status(f"📋 已复制路径: {tool.path}")

    def copy_info(self, tool):
        info = f"工具名称: {tool.name}\n类型: {tool.tool_type}\n分类: {tool.category}\n描述: {tool.description}\n路径: {tool.path}\n启动次数: {tool.launch_count}\n最后启动: {tool.last_launch}"
        QApplication.clipboard().setText(info)
        self.set_status(f"📋 已复制工具 '{tool.name}' 的信息")

    def delete_tool(self, tool):
        from PyQt5.QtWidgets import QMessageBox
        reply = QMessageBox.question(self, "删除工具", f"确定要删除工具 '{tool.name}' 吗？", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.tools = [t for t in self.tools if t != tool]
            self.filtered_tools = [t for t in self.filtered_tools if t != tool]
            self.save_tools()
            self.show_tools()

    def save_tools(self):
        # 保存到config.json
        import json
        data = {"tools": [self.tool_to_dict(t) for t in self.tools]}
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def tool_to_dict(self, tool):
        return {
            "name": tool.name,
            "path": tool.path,
            "tool_type": tool.tool_type,
            "description": tool.description,
            "icon_path": tool.icon_path,
            "category": tool.category,
            "launch_count": tool.launch_count,
            "last_launch": tool.last_launch,
            "args": tool.args
        }

    def get_all_categories(self):
        return [t.category for t in self.tools if t.category]

    def build_category_tree(self):
        self.category_tree.clear()
        # 构建分级分类树
        root = QTreeWidgetItem(["所有工具"])
        root.setData(0, Qt.UserRole, "__all__")
        self.category_tree.addTopLevelItem(root)
        # 收集所有分类
        categories = set(t.category for t in self.tools if t.category)
        # 支持多级分类（用/分隔）
        tree = {}
        for cat in categories:
            parts = cat.split('/')
            cur = tree
            for part in parts:
                if part not in cur:
                    cur[part] = {}
                cur = cur[part]
        def add_items(parent, subtree):
            for k, v in sorted(subtree.items()):
                item = QTreeWidgetItem([k])
                item.setData(0, Qt.UserRole, k)
                parent.addChild(item)
                add_items(item, v)
        add_items(root, tree)
        self.category_tree.expandAll()

    def on_category_clicked(self, item, col=0):
        # 获取完整分类路径
        path = []
        cur = item
        while cur and cur.parent():
            path.insert(0, cur.text(0))
            cur = cur.parent()
        if not path:
            # 所有工具
            self.filtered_tools = self.tools
        else:
            prefix = '/'.join(path)
            self.filtered_tools = [t for t in self.tools if t.category.startswith(prefix)]
        self.show_tools()

    def keyPressEvent(self, event):
        if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_F:
            self.search_input.setFocus()
            self.search_input.selectAll()
        super().keyPressEvent(event)

    def set_status(self, text):
        max_len = 60
        if len(text) > max_len:
            self.status_label.setText(text[:max_len] + "...")
            self.status_label.setToolTip(text)
        else:
            self.status_label.setText(text)
            self.status_label.setToolTip("")

class ToolEditDialog(QDialog):
    TYPE_MAP = [
        ("GUI应用", "exe"),
        ("命令行", "exe"),
        ("java8图形化", "java8_gui"),
        ("java11图形化", "java11_gui"),
        ("java8", "java8"),
        ("java11", "java11"),
        ("python", "python"),
        ("powershell", "powershell"),
        ("批处理", "batch"),
        ("VBS脚本", "vbs"),
        ("网页", "url"),
        ("文件夹", "folder")
    ]
    def __init__(self, parent=None, tool=None, categories=None):
        super().__init__(parent)
        self.setWindowTitle("编辑工具" if tool else "添加工具")
        self.setMinimumWidth(600)
        self.setMinimumHeight(600)
        self.resize(600, 340)
        layout = QVBoxLayout(self)
        # 名称
        self.name_edit = QLineEdit(tool.name if tool else "")
        layout.addWidget(QLabel("工具名称:"))
        layout.addWidget(self.name_edit)
        # 类型（中文显示）
        self.type_combo = QComboBox()
        for zh, en in self.TYPE_MAP:
            self.type_combo.addItem(zh, en)
        if tool:
            # 反查英文到中文
            for i, (zh, en) in enumerate(self.TYPE_MAP):
                if en == tool.tool_type:
                    self.type_combo.setCurrentIndex(i)
                    break
        layout.addWidget(QLabel("工具类型:"))
        layout.addWidget(self.type_combo)
        # 路径
        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit(tool.path if tool else "")
        path_btn = QPushButton("📁")
        path_btn.clicked.connect(self.browse_path)
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(path_btn)
        layout.addWidget(QLabel("工具路径:"))
        layout.addLayout(path_layout)
        # 图标
        icon_layout = QHBoxLayout()
        self.icon_edit = QLineEdit(tool.icon_path if tool else "")
        icon_btn = QPushButton("🖼️")
        icon_btn.clicked.connect(self.browse_icon)
        icon_layout.addWidget(self.icon_edit)
        icon_layout.addWidget(icon_btn)
        layout.addWidget(QLabel("图标路径:"))
        layout.addLayout(icon_layout)
        # 分类（允许自由输入）
        self.category_edit = QLineEdit(tool.category if tool else "")
        layout.addWidget(QLabel("工具分类:"))
        layout.addWidget(self.category_edit)
        # 启动参数
        self.args_edit = QLineEdit(tool.args if tool else "")
        layout.addWidget(QLabel("启动参数:"))
        layout.addWidget(self.args_edit)
        # 描述
        self.desc_edit = QTextEdit(tool.description if tool else "")
        layout.addWidget(QLabel("工具描述:"))
        layout.addWidget(self.desc_edit)
        # 按钮
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)
        # 美化弹窗整体风格
        self.setStyleSheet('''
            QDialog {
                background: #f8fafd;
                border-radius: 16px;
                font-family: "Microsoft YaHei", Arial, sans-serif;
            }
            QLabel {
                font-size: 15px;
                color: #222;
                margin-bottom: 2px;
            }
            QLineEdit, QTextEdit {
                background: #fff;
                border: 1px solid #e0e3e7;
                border-radius: 8px;
                font-size: 15px;
                padding: 8px 10px;
                margin-bottom: 8px;
            }
            QLineEdit:focus, QTextEdit:focus {
                border: 1.5px solid #764ba2;
                background: #f5f6fa;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #667eea, stop:1 #764ba2);
                color: #fff;
                border: none;
                border-radius: 8px;
                font-size: 15px;
                font-weight: bold;
                padding: 8px 0;
                min-width: 60px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #764ba2, stop:1 #667eea);
            }
            QDialogButtonBox QPushButton {
                min-width: 80px;
                margin: 0 8px;
            }
        ''')
    def browse_path(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择工具文件", "", "所有文件 (*)")
        if path:
            self.path_edit.setText(path)
    def browse_icon(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择图标", "", "图标文件 (*.ico *.png *.jpg *.jpeg);;所有文件 (*)")
        if path:
            self.icon_edit.setText(path)
    def get_data(self):
        return {
            "name": self.name_edit.text().strip(),
            "tool_type": self.type_combo.currentData(),
            "path": self.path_edit.text().strip(),
            "icon_path": self.icon_edit.text().strip(),
            "category": self.category_edit.text().strip(),
            "args": self.args_edit.text().strip(),
            "description": self.desc_edit.toPlainText().strip(),
        }

   

def contextMenuEvent(self, event):
    widget = self.childAt(event.pos())
    # 判断是否点击空白区域
    from PyQt5.QtWidgets import QMenu
    menu = QMenu(self)
    if not isinstance(widget, ToolCard):
        add_action = menu.addAction("➕ 添加工具")
        add_action.triggered.connect(self.add_tool)
    menu.exec(event.globalPos())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = QuickStartMainWindow()
    window.show()
    sys.exit(app.exec_()) 
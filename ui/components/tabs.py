from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabBar, QStackedWidget, QTextBrowser, QMessageBox, QMenu, QApplication
from PyQt6.QtCore import pyqtSignal, Qt
import os
from ui.components.editor import TMLScintilla

class EditorTabs(QWidget):
    tab_changed = pyqtSignal(str)  # rel_path
    cursor_changed = pyqtSignal(int, int) # line, col
    file_saved = pyqtSignal(str) # rel_path
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.opened_files = {} # {rel_path: {"editor": TMLScintilla, "full_path": str, "is_doc": bool}}
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.tab_bar = QTabBar()
        self.tab_bar.setTabsClosable(True)
        self.tab_bar.setMovable(True)
        self.tab_bar.setExpanding(False)
        self.tab_bar.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tab_bar.setStyleSheet("""
            QTabBar::tab {
                background: #2d2d2d;
                color: #858585;
                padding: 8px 15px;
                border-right: 1px solid #1e1e1e;
                width: 150px;
            }
            QTabBar::tab:selected {
                background: #1e1e1e;
                color: white;
                border-bottom: 2px solid #4CAF50;
            }
            QTabBar::tab:hover {
                background: #333;
            }
        """)
        
        self.md_viewer = QTextBrowser()
        self.md_viewer.setStyleSheet("""
            QTextBrowser {
                background-color: #272822;
                color: #f8f8f2;
                border: none;
                padding: 20px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
            }
        """)
        self.md_viewer.setOpenExternalLinks(True)
        
        self.stack = QStackedWidget()
        self.stack.addWidget(self.md_viewer) # Index 0
        
        layout.addWidget(self.tab_bar)
        layout.addWidget(self.stack)
        
        self.tab_bar.currentChanged.connect(self._on_tab_changed)
        self.tab_bar.tabCloseRequested.connect(self.close_tab)
        
    def _on_tab_changed(self, index):
        if index == -1:
            self.tab_changed.emit("")
            return
            
        rel_path = self.tab_bar.tabData(index)
        data = self.opened_files.get(rel_path)
        if data:
            if data.get("is_doc"):
                self.stack.setCurrentIndex(0)
                self.md_viewer.setHtml(data.get("content", ""))
            else:
                self.stack.setCurrentWidget(data["editor"])
            self.tab_changed.emit(rel_path)

    def add_editor_tab(self, rel_path, full_path, content):
        if rel_path in self.opened_files:
            self.switch_to_tab(rel_path)
            return self.opened_files[rel_path]["editor"]
            
        editor = TMLScintilla()
        editor.setText(content)
        editor.cursorPositionChanged.connect(lambda l, c: self.cursor_changed.emit(l, c))
        
        self.stack.addWidget(editor)
        self.opened_files[rel_path] = {
            "editor": editor,
            "full_path": full_path,
            "is_doc": False
        }
        
        index = self.tab_bar.addTab(os.path.basename(rel_path))
        self.tab_bar.setTabData(index, rel_path)
        self.tab_bar.setCurrentIndex(index)
        return editor

    def add_doc_tab(self, rel_path, full_path, content, is_markdown=False):
        if rel_path in self.opened_files:
            self.switch_to_tab(rel_path)
            return
            
        html_content = content
        if is_markdown:
            try:
                import markdown
                html_content = markdown.markdown(content, extensions=['fenced_code', 'tables'])
                # Basic styling for dark theme
                html_content = f"""
                <style>
                    body {{ background-color: #272822; color: #f8f8f2; font-family: 'Segoe UI', sans-serif; }}
                    pre {{ background-color: #1e1e1e; padding: 10px; border-radius: 5px; }}
                    code {{ font-family: 'Consolas', monospace; color: #a6e22e; }}
                    h1, h2, h3 {{ color: #4CAF50; }}
                    a {{ color: #66d9ef; text-decoration: none; }}
                    table {{ border-collapse: collapse; width: 100%; }}
                    th, td {{ border: 1px solid #444; padding: 8px; text-align: left; }}
                    th {{ background-color: #333; }}
                </style>
                <body>{html_content}</body>
                """
            except: pass
            
        self.opened_files[rel_path] = {
            "is_doc": True,
            "content": html_content,
            "full_path": full_path
        }
        
        index = self.tab_bar.addTab(os.path.basename(rel_path))
        self.tab_bar.setTabData(index, rel_path)
        self.tab_bar.setCurrentIndex(index)
        self.md_viewer.setHtml(html_content)
        self.stack.setCurrentIndex(0)

    def switch_to_tab(self, rel_path):
        for i in range(self.tab_bar.count()):
            if self.tab_bar.tabData(i) == rel_path:
                self.tab_bar.setCurrentIndex(i)
                return True
        return False

    def rename_tab(self, old_rel_path, new_rel_path, new_full_path):
        if old_rel_path not in self.opened_files:
            return False
            
        data = self.opened_files.pop(old_rel_path)
        data["full_path"] = new_full_path
        self.opened_files[new_rel_path] = data
        
        for i in range(self.tab_bar.count()):
            if self.tab_bar.tabData(i) == old_rel_path:
                self.tab_bar.setTabText(i, os.path.basename(new_rel_path))
                self.tab_bar.setTabData(i, new_rel_path)
                break
        return True

    def close_tab(self, index):
        rel_path = self.tab_bar.tabData(index)
        if not rel_path: return
        
        data = self.opened_files.pop(rel_path, None)
        if data and not data.get("is_doc"):
            editor = data["editor"]
            self.stack.removeWidget(editor)
            editor.deleteLater()
            
        self.tab_bar.removeTab(index)
        
    def current_editor(self):
        index = self.tab_bar.currentIndex()
        if index == -1: return None
        
        rel_path = self.tab_bar.tabData(index)
        data = self.opened_files.get(rel_path)
        if data:
            if data.get("is_doc"):
                return self.md_viewer
            return data.get("editor")
        return None

    def get_editor(self, rel_path):
        data = self.opened_files.get(rel_path)
        if data and not data.get("is_doc"):
            return data["editor"]
        return None

    def current_rel_path(self):
        index = self.tab_bar.currentIndex()
        if index == -1: return ""
        return self.tab_bar.tabData(index) or ""

    def close_current_tab(self):
        index = self.tab_bar.currentIndex()
        if index != -1:
            self.close_tab(index)

    def next_tab(self):
        if self.tab_bar.count() > 1:
            next_idx = (self.tab_bar.currentIndex() + 1) % self.tab_bar.count()
            self.tab_bar.setCurrentIndex(next_idx)

    def prev_tab(self):
        if self.tab_bar.count() > 1:
            prev_idx = (self.tab_bar.currentIndex() - 1) % self.tab_bar.count()
            self.tab_bar.setCurrentIndex(prev_idx)

    def show_context_menu(self, position):
        index = self.tab_bar.tabAt(position)
        if index == -1: return
        
        menu = QMenu()
        close_act = menu.addAction("Close")
        close_others_act = menu.addAction("Close Others")
        close_all_act = menu.addAction("Close All")
        menu.addSeparator()
        copy_path_act = menu.addAction("Copy Relative Path")
        
        action = menu.exec(self.tab_bar.mapToGlobal(position))
        
        if action == close_act:
            self.close_tab(index)
        elif action == close_others_act:
            for i in reversed(range(self.tab_bar.count())):
                if i != index: self.close_tab(i)
        elif action == close_all_act:
            for i in reversed(range(self.tab_bar.count())):
                self.close_tab(i)
        elif action == copy_path_act:
            rel_path = self.tab_bar.tabData(index)
            QApplication.clipboard().setText(rel_path)

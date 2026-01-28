from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTreeWidget, QTabBar, QStackedWidget, QFrame, QListWidget,
                             QTreeWidgetItem, QInputDialog, QMessageBox, QMenu)
from PyQt6.QtCore import Qt, pyqtSignal
import os
import threading

class SidebarWidget(QFrame):
    new_macro_requested = pyqtSignal()
    new_folder_requested = pyqtSignal()
    save_requested = pyqtSignal()
    file_selected = pyqtSignal(object) # item
    doc_selected = pyqtSignal(object) # item
    item_expanded = pyqtSignal(object) # item
    item_renamed = pyqtSignal(str, str) # old_path, new_path
    item_deleted = pyqtSignal(str) # path
    item_moved = pyqtSignal(str, str) # old_path, new_path
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        self.setMinimumWidth(200)
        self.setStyleSheet("background-color: #252526; border-right: 1px solid #333;")
        layout = QVBoxLayout(self)
        
        # Sidebar Tabs
        self.tabs = QTabBar()
        self.tabs.setExpanding(True)
        self.tabs.setStyleSheet("""
            QTabBar::tab {
                background: #2d2d2d;
                color: #858585;
                padding: 6px;
                border-bottom: 1px solid #333;
                font-size: 10px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background: #252526;
                color: white;
                border-bottom: 2px solid #4CAF50;
            }
        """)
        self.tabs.addTab("EXPLORER")
        self.tabs.addTab("DOCS")
        self.tabs.addTab("RUNNING")
        
        self.stack = QStackedWidget()
        
        # Explorer Page
        explorer_page = QWidget()
        explorer_layout = QVBoxLayout(explorer_page)
        explorer_layout.setContentsMargins(0, 0, 0, 0)
        
        self.file_tree = QTreeWidget()
        self.file_tree.setHeaderHidden(True)
        self.file_tree.setDragEnabled(True)
        self.file_tree.setAcceptDrops(True)
        self.file_tree.setDragDropMode(QTreeWidget.DragDropMode.InternalMove)
        self.file_tree.setStyleSheet("""
            QTreeWidget { border: none; background: transparent; color: #ccc; outline: none; }
            QTreeWidget::item { padding: 5px 10px; }
            QTreeWidget::item:selected { background: #37373d; color: white; }
            QTreeWidget::item:hover { background: #2a2d2e; }
        """)
        self.file_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        
        top_btns = QHBoxLayout()
        self.btn_new = QPushButton("New")
        self.btn_new_folder = QPushButton("Folder")
        self.btn_save = QPushButton("Save")
        for btn in [self.btn_new, self.btn_new_folder, self.btn_save]:
            btn.setStyleSheet("""
                QPushButton { background: #3c3c3c; color: #ccc; border: 1px solid #444; padding: 6px; }
                QPushButton:hover { background: #4a4a4a; color: white; }
            """)
        top_btns.addWidget(self.btn_new)
        top_btns.addWidget(self.btn_new_folder)
        top_btns.addWidget(self.btn_save)
        
        explorer_layout.addLayout(top_btns)
        explorer_layout.addWidget(self.file_tree)
        
        # Docs Page
        docs_page = QWidget()
        docs_layout = QVBoxLayout(docs_page)
        docs_layout.setContentsMargins(0, 0, 0, 0)
        self.docs_tree = QTreeWidget()
        self.docs_tree.setHeaderHidden(True)
        self.docs_tree.setStyleSheet(self.file_tree.styleSheet())
        docs_layout.addWidget(self.docs_tree)
        
        # Running Page
        running_page = QWidget()
        running_layout = QVBoxLayout(running_page)
        running_layout.setContentsMargins(0, 0, 0, 0)
        
        # Running list (Threads)
        self.running_tree = QTreeWidget()
        self.running_tree.setHeaderHidden(True)
        self.running_tree.setIndentation(12)
        self.running_tree.setAnimated(True)
        self.running_tree.setStyleSheet(self.file_tree.styleSheet() + """
            QTreeWidget::item {
                padding: 4px;
                border-bottom: 1px solid #2d2d2d;
            }
            QTreeWidget::item:selected {
                background-color: #37373d;
            }
        """)
        self.running_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.running_tree.customContextMenuRequested.connect(self.show_running_context_menu)
        running_layout.addWidget(self.running_tree)
        
        # Categories
        from PyQt6.QtGui import QColor
        self.tml_group = QTreeWidgetItem(self.running_tree, ["TML MACROS"])
        self.tml_group.setForeground(0, QColor("#858585"))
        font = self.tml_group.font(0)
        font.setBold(True)
        font.setPointSize(9)
        self.tml_group.setFont(0, font)
        self.tml_group.setExpanded(True)
        
        self.sys_group = QTreeWidgetItem(self.running_tree, ["SYSTEM THREADS"])
        self.sys_group.setForeground(0, QColor("#858585"))
        self.sys_group.setFont(0, font)
        self.sys_group.setExpanded(False) # Default collapsed for system threads
        
        self.stack.addWidget(explorer_page)
        self.stack.addWidget(docs_page)
        self.stack.addWidget(running_page)
        
        self.tabs.currentChanged.connect(self.stack.setCurrentIndex)
        self.tabs.currentChanged.connect(self.on_tab_changed)
        
        layout.addWidget(self.tabs)
        layout.addWidget(self.stack)

        # Connect internal signals
        self.btn_new.clicked.connect(self.new_macro_requested.emit)
        self.btn_new_folder.clicked.connect(self.new_folder_requested.emit)
        self.btn_save.clicked.connect(self.save_requested.emit)
        self.file_tree.itemClicked.connect(self.file_selected.emit)
        self.file_tree.itemExpanded.connect(self.on_item_expanded)
        self.docs_tree.itemClicked.connect(self.doc_selected.emit)
        self.file_tree.customContextMenuRequested.connect(self.show_tree_context_menu)
        self.file_tree.dropEvent = self.on_tree_drop

    def on_tree_drop(self, event):
        source_item = self.file_tree.currentItem()
        if not source_item:
            return

        target_item = self.file_tree.itemAt(event.position().toPoint())
        source_path = source_item.data(0, Qt.ItemDataRole.UserRole)
        
        if not source_path or not os.path.exists(source_path):
            return

        # Target directory determination
        if target_item:
            target_path = target_item.data(0, Qt.ItemDataRole.UserRole)
            if not target_path:
                target_path = "examples"
            elif not os.path.isdir(target_path):
                target_path = os.path.dirname(target_path)
        else:
            target_path = "examples"

        # Prevent dropping into itself
        if source_path == target_path:
            return
            
        new_path = os.path.join(target_path, os.path.basename(source_path))
        
        if os.path.exists(new_path):
            QMessageBox.warning(self, "Move Error", f"Item already exists at destination: {os.path.basename(source_path)}")
            return

        try:
            import shutil
            shutil.move(source_path, new_path)
            self.item_moved.emit(source_path, new_path)
            self.load_file_list()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not move item: {e}")

    def on_item_expanded(self, item):
        # Lazy load children
        path = item.data(0, Qt.ItemDataRole.UserRole)
        if not path or not os.path.isdir(path):
            return
            
        # Clear dummy
        item.takeChildren()
        self._add_tree_items(item, path)
        self.item_expanded.emit(item)

    def load_file_list(self):
        self.file_tree.clear()
        root_path = "examples"
        if not os.path.exists(root_path):
            os.makedirs(root_path)
            
        root_item = QTreeWidgetItem(self.file_tree)
        root_item.setText(0, "examples")
        root_item.setData(0, Qt.ItemDataRole.UserRole, os.path.abspath(root_path))
        
        # Add actual children (lazy load will handle the rest)
        self._add_tree_items(root_item, root_path)
        root_item.setExpanded(True)

    def load_docs_list(self):
        self.docs_tree.clear()
        docs_path = "docs"
        if not os.path.exists(docs_path):
            return
            
        root_item = QTreeWidgetItem(self.docs_tree)
        root_item.setText(0, "Documentation")
        root_item.setData(0, Qt.ItemDataRole.UserRole, os.path.abspath(docs_path))
        
        self._add_docs_items(root_item, docs_path)
        root_item.setExpanded(True)

    def _add_docs_items(self, parent_item, path):
        try:
            for entry in sorted(os.listdir(path)):
                full_path = os.path.join(path, entry)
                if os.path.isdir(full_path):
                    dir_item = QTreeWidgetItem(parent_item)
                    dir_item.setText(0, entry)
                    dir_item.setData(0, Qt.ItemDataRole.UserRole, os.path.abspath(full_path))
                    self._add_docs_items(dir_item, full_path)
                elif entry.endswith(".md") or entry.endswith(".tml"):
                    file_item = QTreeWidgetItem(parent_item)
                    file_item.setText(0, entry)
                    file_item.setData(0, Qt.ItemDataRole.UserRole, os.path.abspath(full_path))
        except: pass

    def _add_tree_items(self, parent_item, path):
        try:
            for entry in sorted(os.listdir(path)):
                full_path = os.path.join(path, entry)
                if os.path.isdir(full_path):
                    dir_item = QTreeWidgetItem(parent_item)
                    dir_item.setText(0, entry)
                    dir_item.setData(0, Qt.ItemDataRole.UserRole, os.path.abspath(full_path))
                    # Add dummy child for expansion
                    if os.listdir(full_path):
                        QTreeWidgetItem(dir_item)
                elif entry.endswith(".tml"):
                    file_item = QTreeWidgetItem(parent_item)
                    file_item.setText(0, entry)
                    file_item.setData(0, Qt.ItemDataRole.UserRole, os.path.abspath(full_path))
        except: pass

    def show_tree_context_menu(self, position):
        item = self.file_tree.itemAt(position)
        menu = QMenu()
        
        # Determine current directory
        current_dir = "examples"
        if item:
            path = item.data(0, Qt.ItemDataRole.UserRole)
            if os.path.isdir(path):
                current_dir = path
            else:
                current_dir = os.path.dirname(path)
        
        new_file_act = menu.addAction("New Macro")
        new_folder_act = menu.addAction("New Folder")
        menu.addSeparator()
        
        delete_act = None
        rename_act = None
        if item and item.text(0) != "examples":
            rename_act = menu.addAction("Rename")
            delete_act = menu.addAction("Delete")
            menu.addSeparator()
            reveal_act = menu.addAction("Reveal in Explorer")
            copy_path_act = menu.addAction("Copy Full Path")
            
        action = menu.exec(self.file_tree.mapToGlobal(position))
        
        if action == new_file_act:
            self.create_new_at(current_dir)
        elif action == new_folder_act:
            self.create_folder_at(current_dir)
        elif action == rename_act:
            self.rename_item(item)
        elif action == delete_act:
            self.delete_item(item)
        elif action == reveal_act:
            path = item.data(0, Qt.ItemDataRole.UserRole)
            import subprocess
            if os.path.isdir(path):
                subprocess.Popen(f'explorer "{os.path.abspath(path)}"')
            else:
                subprocess.Popen(f'explorer /select,"{os.path.abspath(path)}"')
        elif action == copy_path_act:
            path = item.data(0, Qt.ItemDataRole.UserRole)
            from PyQt6.QtWidgets import QApplication
            QApplication.clipboard().setText(os.path.abspath(path))

    def create_new_at(self, directory):
        name, ok = QInputDialog.getText(self, "New Macro", "Filename (e.g. macro.tml):")
        if ok and name:
            if not name.endswith(".tml"):
                name += ".tml"
            path = os.path.join(directory, name)
            try:
                if os.path.exists(path):
                    QMessageBox.warning(self, "Error", "File already exists!")
                    return
                with open(path, "w", encoding="utf-8") as f:
                    f.write("")
                self.load_file_list()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not create file: {e}")

    def create_folder_at(self, directory):
        name, ok = QInputDialog.getText(self, "New Folder", "Folder Name:")
        if ok and name:
            path = os.path.join(directory, name)
            try:
                os.makedirs(path, exist_ok=True)
                self.load_file_list()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not create folder: {e}")

    def on_tab_changed(self, index):
        if index == 2: # RUNNING tab
            self.update_running_list()

    def update_running_list(self):
        # Store what was selected and expanded
        # expanded_tml = self.tml_group.isExpanded()
        # expanded_sys = self.sys_group.isExpanded()
        
        # Clear children
        for i in reversed(range(self.tml_group.childCount())):
            self.tml_group.removeChild(self.tml_group.child(i))
        for i in reversed(range(self.sys_group.childCount())):
            self.sys_group.removeChild(self.sys_group.child(i))
        
        # Get all threads
        threads = threading.enumerate()
        
        from PyQt6.QtWidgets import QTreeWidgetItem
        from PyQt6.QtGui import QColor, QIcon
        from PyQt6.QtCore import Qt
        
        tml_threads = [t for t in threads if t.name.startswith("TML-")]
        program_threads = [t for t in threads if not t.name.startswith("TML-")]
        
        # Update TML Macros
        if tml_threads:
            self.tml_group.setText(0, f"TML MACROS ({len(tml_threads)})")
            for t in tml_threads:
                item = QTreeWidgetItem(self.tml_group, [f"  ▶ {t.name}"])
                item.setToolTip(0, f"ID: {t.ident}\nStatus: Running")
                item.setData(0, Qt.ItemDataRole.UserRole, t.name)
                item.setForeground(0, QColor("#4CAF50")) # Green for running
        else:
            self.tml_group.setText(0, "TML MACROS (0)")
            item = QTreeWidgetItem(self.tml_group, ["  No active macros"])
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            item.setForeground(0, QColor("#666666"))
        
        # Update System Threads
        self.sys_group.setText(0, f"SYSTEM THREADS ({len(program_threads)})")
        for t in program_threads:
            name = t.name
            if name == "MainThread":
                name = "MainThread (UI)"
            
            item = QTreeWidgetItem(self.sys_group, [f"  ⚙ {name}"])
            item.setToolTip(0, f"ID: {t.ident}")
            item.setData(0, Qt.ItemDataRole.UserRole, t.name)
            
            if t.name == "MainThread":
                item.setForeground(0, QColor("#4FC3F7")) # Light blue for UI thread
            else:
                item.setForeground(0, QColor("#cccccc"))

    def show_running_context_menu(self, position):
        item = self.running_tree.itemAt(position)
        if not item or item in [self.tml_group, self.sys_group]:
            return
            
        thread_name = item.data(0, Qt.ItemDataRole.UserRole)
        if not thread_name:
            return
            
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #252526;
                color: #cccccc;
                border: 1px solid #454545;
            }
            QMenu::item:selected {
                background-color: #094771;
            }
        """)
        
        if thread_name.startswith("TML-Run-"):
            macro_name = thread_name.replace("TML-Run-", "")
            stop_act = menu.addAction(f"Stop Macro: {macro_name}")
            action = menu.exec(self.running_tree.mapToGlobal(position))
            
            if action == stop_act:
                # Access controller via parent (MacroEditorWindow)
                target = self.parent()
                while target and not hasattr(target, "controller"):
                    target = target.parent()
                
                if target and hasattr(target, "controller"):
                    target.controller.stop_macro(macro_name)
        
        elif thread_name.startswith("TML-Comp-"):
            menu.addAction("Compilation in progress...").setEnabled(False)
            menu.exec(self.running_tree.mapToGlobal(position))
        else:
            menu.addAction(f"Thread: {thread_name}").setEnabled(False)
            menu.exec(self.running_tree.mapToGlobal(position))

    def delete_item(self, item):
        path = item.data(0, Qt.ItemDataRole.UserRole)
        if not path: return
        
        reply = QMessageBox.question(self, "Confirm Delete", 
                                   f"Are you sure you want to delete {os.path.basename(path)}?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                import shutil
                self.item_deleted.emit(path) # Notify editor to close tabs
                
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                
                self.load_file_list()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not delete: {e}")

    def rename_item(self, item):
        old_path = item.data(0, Qt.ItemDataRole.UserRole)
        if not old_path: return
        
        old_name = os.path.basename(old_path)
        new_name, ok = QInputDialog.getText(self, "Rename", "New Name:", text=old_name)
        
        if ok and new_name and new_name != old_name:
            new_path = os.path.join(os.path.dirname(old_path), new_name)
            try:
                os.rename(old_path, new_path)
                self.item_renamed.emit(old_path, new_path)
                self.load_file_list()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not rename: {e}")

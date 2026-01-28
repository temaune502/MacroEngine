import os
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QListWidget, QTextEdit, 
                             QLineEdit, QSplitter, QListWidgetItem, QMessageBox, QFrame,
                             QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox, QComboBox,
                             QTreeWidget, QTreeWidgetItem, QInputDialog, QMenu, QTabBar, QStackedWidget, QTextBrowser)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor, QShortcut, QKeySequence
from PyQt6.Qsci import QsciScintilla, QsciLexerPython, QsciAPIs
from services.config_manager import ConfigManager
import time
from ui.components.editor import TMLScintilla
from ui.components.sidebar import SidebarWidget
from ui.components.console import ConsoleWidget
from .components.tabs import EditorTabs
from .components.search import SearchWidget
from .components.runtime_manager import RuntimeManager

class MacroEditorWindow(QMainWindow):
    def __init__(self, controller, main_window):
        super().__init__()
        self.controller = controller
        self.main_window = main_window
        self.setWindowTitle("TML Advanced Editor")
        self.resize(1100, 750)
        self.current_file = None
        self.last_vars_state = {} # Store last state of variables for logging
        self.last_total_instr = 0
        self.last_stats_time = time.time()
        
        self.runtime_manager = RuntimeManager(controller, self)
        self.runtime_manager.stats_updated.connect(self.on_stats_updated)
        
        self.setup_ui()
        
        # Sidebar initial load
        self.sidebar.load_file_list()
        self.sidebar.load_docs_list()
        
        # Open empty file on start
        self.on_new()

    def setup_ui(self):
        ACCENT = "#4CAF50"
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet("QSplitter::handle { background-color: #333; }")
        
        # Sidebar
        self.sidebar = SidebarWidget(self)
        self.sidebar.file_selected.connect(self.on_file_selected)
        self.sidebar.doc_selected.connect(self.on_doc_selected)
        self.sidebar.item_expanded.connect(self.on_item_expanded)
        self.sidebar.new_macro_requested.connect(self.on_new)
        self.sidebar.new_folder_requested.connect(self.on_new_folder)
        self.sidebar.save_requested.connect(self.on_save)
        self.sidebar.item_renamed.connect(self.on_item_renamed)
        self.sidebar.item_deleted.connect(self.on_item_deleted)
        self.sidebar.item_moved.connect(self.on_item_moved)
        
        # Sidebar hotkey binding
        self.hotkey_panel = QFrame()
        self.hotkey_panel.setStyleSheet("background: #1e1e1e; border-top: 1px solid #333;")
        hotkey_layout = QVBoxLayout(self.hotkey_panel)
        hotkey_layout.setContentsMargins(10, 10, 10, 10)
        
        lbl_hotkey = QLabel("GLOBAL HOTKEY")
        lbl_hotkey.setStyleSheet("color: #858585; font-weight: bold; font-size: 10px; margin-bottom: 5px;")
        
        self.hotkey_input = QLineEdit()
        self.hotkey_input.setPlaceholderText("e.g. ctrl+1, f2")
        self.hotkey_input.setStyleSheet("""
            QLineEdit { background: #3c3c3c; border: 1px solid #555; color: white; padding: 6px; font-family: 'Consolas'; }
            QLineEdit:focus { border: 1px solid #007acc; }
        """)
        
        self.btn_bind = QPushButton("Apply Binding")
        self.btn_bind.setStyleSheet(f"""
            QPushButton {{ background: {ACCENT}; color: white; font-weight: bold; padding: 8px; border: none; }}
            QPushButton:hover {{ background: #45a049; }}
        """)
        self.btn_bind.clicked.connect(self.on_bind)
        
        hotkey_layout.addWidget(lbl_hotkey)
        hotkey_layout.addWidget(self.hotkey_input)
        hotkey_layout.addWidget(self.btn_bind)
        
        self.sidebar.layout().addWidget(self.hotkey_panel)
        
        # Right editor area
        editor_area = QWidget()
        editor_area_layout = QVBoxLayout(editor_area)
        editor_area_layout.setContentsMargins(0, 0, 0, 0)
        editor_area_layout.setSpacing(0)
        
        toolbar = QFrame()
        toolbar.setFixedHeight(40)
        toolbar.setStyleSheet("background-color: #2d2d2d; border-bottom: 1px solid #333;")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(10, 0, 10, 0)
        
        self.lbl_current_file = QLabel("No file open")
        self.lbl_current_file.setStyleSheet("color: #ccc; font-weight: bold;")
        
        # Speed Control
        self.speed_combo = QComboBox()
        self.speed_combo.setFixedWidth(160)
        self.speed_combo.addItems([
            "5 inst/tick", 
            "50 inst/tick", 
            "100 inst/tick", 
            "250 inst/tick", 
            "500 inst/tick (0.5x)", 
            "1000 inst/tick (1x)", 
            "2000 inst/tick (2x)", 
            "5000 inst/tick (5x)", 
            "Max (No Limit)"
        ])
        self.speed_combo.setCurrentIndex(5)
        self.speed_combo.setStyleSheet("""
            QComboBox { 
                background: #3c3c3c; 
                color: #ccc; 
                border: 1px solid #444; 
                padding: 4px; 
                border-radius: 2px;
                font-size: 11px;
            }
            QComboBox:hover { background: #4a4a4a; }
            QComboBox QAbstractItemView { background: #2d2d2d; color: #ccc; selection-background-color: #007acc; }
        """)
        self.speed_combo.currentIndexChanged.connect(self.on_speed_changed)
        
        self.btn_run = QPushButton("▶ Run")
        self.btn_run.setFixedWidth(80)
        self.btn_run.setStyleSheet("""
            QPushButton { background: #4CAF50; color: white; border: none; padding: 5px; font-weight: bold; border-radius: 2px; }
            QPushButton:hover { background: #45a049; }
        """)
        self.btn_run.clicked.connect(self.on_run)

        self.btn_stop = QPushButton("■ Stop")
        self.btn_stop.setFixedWidth(80)
        self.btn_stop.setStyleSheet("""
            QPushButton { background: #f44336; color: white; border: none; padding: 5px; font-weight: bold; border-radius: 2px; }
            QPushButton:hover { background: #d32f2f; }
        """)
        self.btn_stop.clicked.connect(self.on_stop)
        
        toolbar_layout.addWidget(self.lbl_current_file)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(QLabel("Speed:"))
        toolbar_layout.addWidget(self.speed_combo)
        toolbar_layout.addSpacing(10)
        toolbar_layout.addWidget(self.btn_run)
        toolbar_layout.addWidget(self.btn_stop)
        
        # Tabs Manager
        self.tabs = EditorTabs(self)
        self.tabs.tab_changed.connect(self.on_tab_changed)
        self.tabs.cursor_changed.connect(self.on_cursor_changed)
        self.tabs.tab_bar.customContextMenuRequested.connect(self.tabs.show_context_menu)
        
        # Console
        self.console_widget = ConsoleWidget(self)
        self.console_widget.btn_clear.clicked.connect(lambda: self.console_widget.clear())
        self.console_widget.console.anchorClicked.connect(self.on_console_link_clicked)
        
        # Splitter for Editor and Console
        self.editor_splitter = QSplitter(Qt.Orientation.Vertical)
        self.editor_splitter.setStyleSheet("QSplitter::handle { background-color: #333; height: 2px; }")
        self.editor_splitter.addWidget(self.tabs)
        self.editor_splitter.addWidget(self.console_widget)
        self.editor_splitter.setStretchFactor(0, 3)
        self.editor_splitter.setStretchFactor(1, 1)
        self.editor_splitter.setSizes([600, 200])
        
        # Search Bar
        self.search_widget = SearchWidget(self.get_current_editor, self)
        self.search_widget.setVisible(False)
        
        editor_area_layout.addWidget(toolbar)
        editor_area_layout.addWidget(self.search_widget)
        editor_area_layout.addWidget(self.editor_splitter)
        
        splitter.addWidget(self.sidebar)
        splitter.addWidget(editor_area)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 4)
        splitter.setSizes([250, 850])
        
        layout.addWidget(splitter)
        
        # Shortcuts
        self.search_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        self.search_shortcut.activated.connect(self.search_widget.show_search)
        self.replace_shortcut = QShortcut(QKeySequence("Ctrl+H"), self)
        self.replace_shortcut.activated.connect(self.search_widget.show_search) # Same panel
        self.esc_shortcut = QShortcut(QKeySequence("Esc"), self)
        self.esc_shortcut.activated.connect(self.search_widget.hide_search)
        
        # Status Bar
        self.status_bar = self.statusBar()
        self.status_bar.setStyleSheet("background-color: #1e1e1e; color: #858585; border-top: 1px solid #333; min-height: 22px;")
        
        self.lbl_status_pos = QLabel("Line: 1, Col: 1")
        self.lbl_status_info = QLabel("Ready")
        self.lbl_status_stats = QLabel("IPS: 0 | Total: 0")
        
        self.lbl_status_pos.setStyleSheet("margin-right: 20px; font-family: 'Consolas'; font-size: 11px;")
        self.lbl_status_info.setStyleSheet("font-weight: bold; font-size: 11px;")
        self.lbl_status_stats.setStyleSheet("margin-right: 20px; font-family: 'Consolas'; font-size: 11px;")
        
        self.status_bar.addPermanentWidget(self.lbl_status_pos)
        self.status_bar.addPermanentWidget(self.lbl_status_stats)
        self.status_bar.addWidget(self.lbl_status_info)
        
        # Shortcuts (more)
        self.save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        self.save_shortcut.activated.connect(self.on_save)
        
        self.comment_shortcut = QShortcut(QKeySequence("Ctrl+/"), self)
        self.comment_shortcut.activated.connect(self.on_toggle_comment)
        
        self.duplicate_shortcut = QShortcut(QKeySequence("Ctrl+D"), self)
        self.duplicate_shortcut.activated.connect(self.on_duplicate_line)

        self.goto_line_shortcut = QShortcut(QKeySequence("Ctrl+G"), self)
        self.goto_line_shortcut.activated.connect(self.on_goto_line)
        
        self.clear_console_shortcut = QShortcut(QKeySequence("Ctrl+L"), self)
        self.clear_console_shortcut.activated.connect(self.console_widget.clear)

        self.move_up_shortcut = QShortcut(QKeySequence("Alt+Up"), self)
        self.move_up_shortcut.activated.connect(self.on_move_line_up)
        self.move_down_shortcut = QShortcut(QKeySequence("Alt+Down"), self)
        self.move_down_shortcut.activated.connect(self.on_move_line_down)

        # Memory Inspector and Running Macros Timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_memory_inspector)
        self.update_timer.timeout.connect(self.update_running_macros)
        self.update_timer.start(500) # Update every 500ms

    def get_current_editor(self):
        return self.tabs.current_editor()

    def close_tab(self, index):
        self.tabs.close_tab(index)

    def on_tab_changed(self, rel_path):
        if not rel_path:
            self.current_file = None
            self.lbl_current_file.setText("No file open")
            self.lbl_status_pos.setText("")
            self.hotkey_input.setText("")
            return
            
        self.current_file = rel_path
        self.lbl_current_file.setText(rel_path)
        
        editor = self.get_current_editor()
        
        # Update status bar position for new editor
        if editor and not isinstance(editor, QTextBrowser):
            self.on_cursor_changed(*editor.getCursorPosition())
        else:
            self.lbl_status_pos.setText("")
        
        config = ConfigManager.load()
        self.hotkey_input.setText(config["hotkeys"].get(rel_path, ""))
        
        # Highlight in tree
        self.highlight_file_in_tree(rel_path)

    def highlight_file_in_tree(self, rel_path):
        # Helper to find and select item by path
        full_path = os.path.join("examples", rel_path).replace("/", os.sep).replace("\\", os.sep)
        
        def find_item(parent_item):
            for i in range(parent_item.childCount()):
                child = parent_item.child(i)
                child_path = child.data(0, Qt.ItemDataRole.UserRole)
                if child_path and os.path.abspath(child_path) == os.path.abspath(full_path):
                    self.sidebar.file_tree.setCurrentItem(child)
                    return True
                if find_item(child):
                    return True
            return False

        # Start from invisible root
        find_item(self.sidebar.file_tree.invisibleRootItem())

    def on_console_link_clicked(self, url):
        url_str = url.toString()
        if url_str.startswith("line:"):
            try:
                line = int(url_str.split(":")[1]) - 1
                editor = self.get_current_editor()
                if editor and not isinstance(editor, QTextBrowser):
                    editor.setCursorPosition(line, 0)
                    editor.setFocus()
                    # Optional: highlight the line temporarily
                    editor.setSelection(line, 0, line, editor.lineLength(line))
            except:
                pass

    def on_cursor_changed(self, line, index):
        editor = self.get_current_editor()
        if not editor or isinstance(editor, QTextBrowser):
            return
        self.lbl_status_pos.setText(f"Line: {line + 1}, Col: {index + 1}")

    def on_toggle_comment(self):
        editor = self.get_current_editor()
        if editor and not isinstance(editor, QTextBrowser):
            editor.toggle_comment()

    def on_duplicate_line(self):
        editor = self.get_current_editor()
        if editor and not isinstance(editor, QTextBrowser):
            editor.duplicate_line()

    def on_move_line_up(self):
        editor = self.get_current_editor()
        if editor and not isinstance(editor, QTextBrowser):
            editor.move_line_up()

    def on_move_line_down(self):
        editor = self.get_current_editor()
        if editor and not isinstance(editor, QTextBrowser):
            editor.move_line_down()

    def on_goto_line(self):
        editor = self.get_current_editor()
        if not editor or isinstance(editor, QTextBrowser):
            return
            
        line, ok = QInputDialog.getInt(self, "Go to Line", "Enter line number:", 
                                     value=editor.getCursorPosition()[0] + 1,
                                     min=1, max=editor.lines())
        if ok:
            editor.setCursorPosition(line - 1, 0)
            editor.setFocus()
            editor.ensureLineVisible(line - 1)

    def on_item_moved(self, source_path, new_path):
        """Update tabs when a file or directory is moved via drag & drop."""
        old_abs_base = os.path.abspath(source_path)
        new_abs_base = os.path.abspath(new_path)
        
        to_update = []
        for rel_path, data in self.tabs.opened_files.items():
            if not data.get("full_path"): continue
            abs_p = os.path.abspath(data["full_path"])
            if abs_p == old_abs_base or abs_p.startswith(old_abs_base + os.sep):
                to_update.append(rel_path)
        
        for old_rel in to_update:
            data = self.tabs.opened_files.pop(old_rel)
            old_abs = os.path.abspath(data["full_path"])
            new_abs = old_abs.replace(old_abs_base, new_abs_base, 1)
            new_rel = os.path.relpath(new_abs, "examples").replace("\\", "/")
            
            data["full_path"] = new_abs
            self.tabs.opened_files[new_rel] = data
            
            # Update tab text and data
            for i in range(self.tabs.tab_bar.count()):
                if self.tabs.tab_bar.tabData(i) == old_rel:
                    self.tabs.tab_bar.setTabText(i, os.path.basename(new_rel))
                    self.tabs.tab_bar.setTabData(i, new_rel)
                    break
            
            if self.current_file == old_rel:
                self.current_file = new_rel
                self.lbl_current_file.setText(new_rel)

        self.main_window.refresh_macros()

    def on_doc_selected(self, item):
        path = item.data(0, Qt.ItemDataRole.UserRole)
        if not path or os.path.isdir(path):
            return
            
        rel_path = os.path.relpath(path, "docs").replace("\\", "/")
        
        # Check if already open
        if rel_path in self.tabs.opened_files:
            self.tabs.switch_to_tab(rel_path)
            return
            
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Markdown or TML?
            is_md = path.endswith(".md")
            self.tabs.add_doc_tab(rel_path, path, content, is_md)
            
            self.current_file = rel_path
            self.lbl_current_file.setText(rel_path)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not load doc: {e}")

    def on_item_expanded(self, item):
        # Already handled by SidebarWidget internally, 
        # but we could add window-specific logic here if needed
        pass

    def on_file_selected(self, item):
        path = item.data(0, Qt.ItemDataRole.UserRole)
        if not path or os.path.isdir(path):
            return
            
        rel_path = os.path.relpath(path, "examples").replace("\\", "/")
        
        # Check if already open
        if rel_path in self.tabs.opened_files:
            self.tabs.switch_to_tab(rel_path)
            return
        
        # Open new tab
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read().replace("\r\n", "\n")
            
            self.tabs.add_editor_tab(rel_path, path, content)
            
            self.current_file = rel_path
            self.lbl_current_file.setText(rel_path)
            
            config = ConfigManager.load()
            self.hotkey_input.setText(config["hotkeys"].get(rel_path, ""))
            self.console_widget.console.append(f"[Editor] Opened {rel_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not load file: {e}")

    def on_new(self):
        # Create a new untitled tab
        count = 1
        while f"Untitled-{count}.tml" in self.tabs.opened_files:
            count += 1
        rel_path = f"Untitled-{count}.tml"
        
        # Load template if exists
        template_path = "template.tml"
        content = ""
        if os.path.exists(template_path):
            try:
                with open(template_path, "r", encoding="utf-8") as f:
                    content = f.read().replace("\r\n", "\n")
            except Exception as e:
                self.console_widget.console.append(f"[Editor] Error loading template: {e}")
        
        self.tabs.add_editor_tab(rel_path, None, content)
        
        self.current_file = rel_path
        self.lbl_current_file.setText(rel_path)
        self.hotkey_input.setText("")
        self.sidebar.file_tree.clearSelection()
        self.last_vars_state = {}

    def on_run(self):
        if not self.current_file:
            return
            
        data = self.tabs.opened_files.get(self.current_file)
        if (data and data.get("is_doc")) or isinstance(self.get_current_editor(), QTextBrowser):
            self.console_widget.console.append("[Editor] Cannot run documentation files!")
            return

        # Autosave
        if self.current_file and not self.current_file.startswith("Untitled-"):
            self.on_save()

        editor = self.get_current_editor()
        if not editor: return
            
        source = editor.text()
        speed_map = {0: 5, 1: 50, 2: 100, 3: 250, 4: 500, 5: 1000, 6: 2000, 7: 5000, 8: 1000000}
        limit = speed_map.get(self.speed_combo.currentIndex(), 1000)
        
        self.runtime_manager.run_macro(self.current_file, source, limit)

    def on_stop(self):
        self.runtime_manager.stop_macro(self.current_file)

    def on_speed_changed(self, index):
        speed_map = {0: 5, 1: 50, 2: 100, 3: 250, 4: 500, 5: 1000, 6: 2000, 7: 5000, 8: 1000000}
        limit = speed_map.get(index, 1000)
        
        if self.current_file:
            self.runtime_manager.apply_initial_speed(self.current_file, limit)
        
        self.console_widget.console.append(f"[Editor] Execution speed set to {self.speed_combo.currentText()}")

    def on_stats_updated(self, ips, total_instr):
        self.lbl_status_stats.setText(f"IPS: {ips:,} | Total: {total_instr:,}")

    def on_bind(self):
        if not self.current_file:
            QMessageBox.warning(self, "Warning", "Select a file first!")
            return
            
        # Check if it's documentation
        data = self.tabs.opened_files.get(self.current_file)
        if data and data.get("is_doc"):
            self.console_widget.console.append("[Editor] Cannot bind documentation files!")
            return
            
        raw_hotkey = self.hotkey_input.text().strip().lower()
        if not raw_hotkey:
            # Allow clearing hotkey
            config = ConfigManager.load()
            if self.current_file in config["hotkeys"]:
                del config["hotkeys"][self.current_file]
                ConfigManager.save(config)
                if hasattr(self.main_window, 'on_hotkeys_updated'):
                    self.main_window.on_hotkeys_updated()
                self.main_window.refresh_macros()
                self.console_widget.console.append(f"[Editor] Unbound {self.current_file}")
            return

        # Normalize hotkey for comparison
        parts = raw_hotkey.replace(" ", "").split('+')
        norm_parts = []
        for p in parts:
            p = p.replace("ctrl_l", "ctrl").replace("ctrl_r", "ctrl")
            p = p.replace("shift_l", "shift").replace("shift_r", "shift")
            p = p.replace("alt_l", "alt").replace("alt_r", "alt").replace("alt_gr", "alt")
            if p: norm_parts.append(p)
        
        norm_parts.sort()
        normalized_hotkey = "+".join(norm_parts)
        
        # Check for duplicates
        config = ConfigManager.load()
        duplicates = []
        for file, hk in config["hotkeys"].items():
            if file == self.current_file:
                continue
            
            # Normalize existing hotkey for comparison
            hk_parts = hk.lower().replace(" ", "").split('+')
            hk_norm = sorted([p.replace("_l", "").replace("_r", "") for p in hk_parts if p])
            if "+".join(hk_norm) == normalized_hotkey:
                duplicates.append(file)
        
        if duplicates:
            msg = f"Hotkey '{normalized_hotkey}' is already used by:\n" + "\n".join(duplicates)
            msg += "\n\nDo you want to bind it anyway? (Multiple macros will trigger)"
            reply = QMessageBox.question(self, "Duplicate Hotkey", msg, 
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                return

        config["hotkeys"][self.current_file] = normalized_hotkey
        ConfigManager.save(config)
        
        if hasattr(self.main_window, 'on_hotkeys_updated'):
            self.main_window.on_hotkeys_updated()
            
        self.main_window.refresh_macros()
        self.console_widget.console.append(f"[Editor] Bound {self.current_file} to '{normalized_hotkey}'")

    def on_item_renamed(self, old_path, new_path):
        """Handle file rename from sidebar."""
        old_abs = os.path.abspath(old_path)
        new_abs = os.path.abspath(new_path)
        
        old_rel = os.path.relpath(old_abs, "examples").replace("\\", "/")
        new_rel = os.path.relpath(new_abs, "examples").replace("\\", "/")
        
        if old_rel in self.tabs.opened_files:
            data = self.tabs.opened_files.pop(old_rel)
            data["full_path"] = new_abs
            self.tabs.opened_files[new_rel] = data
            
            # Update tab text and data
            for i in range(self.tabs.tab_bar.count()):
                if self.tabs.tab_bar.tabData(i) == old_rel:
                    self.tabs.tab_bar.setTabText(i, os.path.basename(new_rel))
                    self.tabs.tab_bar.setTabData(i, new_rel)
                    break
            
            if self.current_file == old_rel:
                self.current_file = new_rel
                self.lbl_current_file.setText(new_rel)

        self.main_window.refresh_macros()

    def on_item_deleted(self, path):
        """Handle file deletion from sidebar."""
        abs_path = os.path.abspath(path)
        rel_path = os.path.relpath(abs_path, "examples").replace("\\", "/")
        
        # Close tab if open
        for i in range(self.tabs.tab_bar.count()):
            if self.tabs.tab_bar.tabData(i) == rel_path:
                self.tabs.close_tab(i)
                break
        
        self.main_window.refresh_macros()

    def on_new_folder(self):
        # Determine parent folder from selection
        parent_dir = "examples"
        selected = self.sidebar.file_tree.selectedItems()
        if selected:
            item_path = selected[0].data(0, Qt.ItemDataRole.UserRole)
            if os.path.isdir(item_path):
                parent_dir = item_path
            else:
                parent_dir = os.path.dirname(item_path)
        
        self.sidebar.create_folder_at(parent_dir)

    def on_save(self):
        editor = self.get_current_editor()
        if not editor or isinstance(editor, QTextBrowser):
            return
        
        # Check if it's documentation (read-only)
        data = self.tabs.opened_files.get(self.current_file)
        if data and data.get("is_doc"):
            return

        if not self.current_file or self.current_file.startswith("Untitled-"):
            # Determine parent folder from selection
            parent_dir = "examples"
            selected = self.sidebar.file_tree.selectedItems()
            if selected:
                item_path = selected[0].data(0, Qt.ItemDataRole.UserRole)
                if item_path:
                    if os.path.isdir(item_path):
                        parent_dir = item_path
                    else:
                        parent_dir = os.path.dirname(item_path)
            
            name, ok = QInputDialog.getText(self, "Save Macro", "Enter filename (e.g. macro.tml):")
            if not ok or not name:
                return
            if not name.endswith(".tml"):
                name += ".tml"
            
            # Combine parent_dir and name
            full_path = os.path.join(parent_dir, name)
            old_rel_path = self.current_file
            new_rel_path = os.path.relpath(full_path, "examples").replace("\\", "/")
            
            # Update Tabs data via helper
            self.tabs.rename_tab(old_rel_path, new_rel_path, full_path)
            
            self.current_file = new_rel_path
            self.lbl_current_file.setText(self.current_file)

        path = os.path.join("examples", self.current_file)
        content = editor.text()
        
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            with open(path, "w", encoding="utf-8", newline='\n') as f:
                f.write(content)
            
            self.sidebar.load_file_list()
            self.main_window.refresh_macros()
            self.console_widget.console.append(f"[Editor] Saved {self.current_file}")
            
            # Highlight in tree
            self.highlight_file_in_tree(self.current_file)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not save file: {e}")

    def update_memory_inspector(self):
        self.update_highlighting()
        self.runtime_manager.update_stats()
        
        status_text, status_color = self.runtime_manager.get_status(self.current_file)
        self.lbl_status_info.setText(status_text)
        self.lbl_status_info.setStyleSheet(f"color: {status_color}; font-weight: bold; font-size: 11px;")

        if not self.current_file:
            self.console_widget.memory_inspector.setRowCount(0)
            self.last_vars_state = {}
            return

        runtime = None
        with self.controller.lock:
            if self.current_file in self.controller.runtimes:
                runtime = self.controller.runtimes[self.current_file]

        if not runtime:
            self.console_widget.memory_inspector.setRowCount(0)
            self.last_vars_state = {}
            return

        if runtime.error:
            self.runtime_manager.handle_runtime_error(self.current_file, runtime.error)
            runtime.error = None
            return

        self.last_vars_state = self.console_widget.update_memory(runtime, self.current_file, self.last_vars_state)

    def update_highlighting(self):
        editor = self.get_current_editor()
        if not editor or isinstance(editor, QTextBrowser):
            return
        
        editor.markerDeleteAll(1)
        
        if not self.console_widget.cb_highlight_execution.isChecked() or not self.current_file:
            return
            
        runtime = None
        with self.controller.lock:
            if self.current_file in self.controller.runtimes:
                runtime = self.controller.runtimes[self.current_file]
                
        if not runtime: return
            
        vm = runtime.vm
        if not vm or not vm.frames: return
            
        frame = vm.frames[-1]
        chunk = frame.function.chunk if frame.function else vm.chunk
        lines = getattr(chunk, 'lines', None)
        if not chunk or not lines: return
            
        idx = frame.ip
        if idx >= len(lines): idx = len(lines) - 1
            
        if idx >= 0:
            line_num = lines[idx]
            if line_num is not None:
                editor.markerAdd(line_num - 1, 1)

    def update_running_macros(self):
        # Update running list in sidebar if RUNNING tab is active
        if self.sidebar.tabs.currentIndex() == 2:
            self.sidebar.update_running_list()

    def on_stdout_written(self, text):
        self.console_widget.console.moveCursor(self.console_widget.console.textCursor().MoveOperation.End)
        self.console_widget.console.insertPlainText(text)
        self.console_widget.console.moveCursor(self.console_widget.console.textCursor().MoveOperation.End)

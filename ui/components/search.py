from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFrame, QTextBrowser)
from PyQt6.QtCore import Qt, pyqtSignal

class SearchWidget(QFrame):
    closed = pyqtSignal()
    
    def __init__(self, get_editor_func, parent=None):
        super().__init__(parent)
        self.get_editor = get_editor_func
        self.setup_ui()
        
    def setup_ui(self):
        self.setFixedHeight(80)
        self.setStyleSheet("background-color: #333; border-bottom: 1px solid #444;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(5)
        
        # Row 1: Find
        row1 = QHBoxLayout()
        lbl_search = QLabel("Find:   ")
        lbl_search.setFixedWidth(50)
        lbl_search.setStyleSheet("color: #ccc;")
        self.search_input = QLineEdit()
        self.search_input.setStyleSheet("background: #1e1e1e; color: white; border: 1px solid #555; padding: 4px;")
        self.search_input.returnPressed.connect(self.on_find_next)
        
        self.btn_find_prev = QPushButton("Previous")
        self.btn_find_next = QPushButton("Next")
        self.btn_close_search = QPushButton("✕")
        
        for btn in [self.btn_find_prev, self.btn_find_next, self.btn_close_search]:
            btn.setStyleSheet("QPushButton { background: #444; color: #ccc; border: 1px solid #555; padding: 4px 10px; } QPushButton:hover { background: #555; }")
            
        self.btn_close_search.setFixedWidth(30)
        self.btn_close_search.setStyleSheet("QPushButton { background: transparent; color: #888; font-size: 16px; border: none; } QPushButton:hover { color: white; }")
        
        self.btn_find_prev.clicked.connect(self.on_find_prev)
        self.btn_find_next.clicked.connect(self.on_find_next)
        self.btn_close_search.clicked.connect(self.hide_search)
        
        row1.addWidget(lbl_search)
        row1.addWidget(self.search_input)
        row1.addWidget(self.btn_find_prev)
        row1.addWidget(self.btn_find_next)
        row1.addWidget(self.btn_close_search)
        
        # Row 2: Replace
        row2 = QHBoxLayout()
        lbl_replace = QLabel("Replace:")
        lbl_replace.setFixedWidth(50)
        lbl_replace.setStyleSheet("color: #ccc;")
        self.replace_input = QLineEdit()
        self.replace_input.setStyleSheet("background: #1e1e1e; color: white; border: 1px solid #555; padding: 4px;")
        
        self.btn_replace = QPushButton("Replace")
        self.btn_replace_all = QPushButton("Replace All")
        for btn in [self.btn_replace, self.btn_replace_all]:
            btn.setStyleSheet("QPushButton { background: #444; color: #ccc; border: 1px solid #555; padding: 4px 10px; } QPushButton:hover { background: #555; }")
            
        self.btn_replace.clicked.connect(self.on_replace)
        self.btn_replace_all.clicked.connect(self.on_replace_all)
        
        row2.addWidget(lbl_replace)
        row2.addWidget(self.replace_input)
        row2.addWidget(self.btn_replace)
        row2.addWidget(self.btn_replace_all)
        row2.addStretch()
        
        layout.addLayout(row1)
        layout.addLayout(row2)

    def show_search(self):
        self.setVisible(True)
        self.search_input.setFocus()
        self.search_input.selectAll()

    def hide_search(self):
        self.setVisible(False)
        editor = self.get_editor()
        if editor:
            editor.setFocus()
        self.closed.emit()

    def on_find_next(self):
        text = self.search_input.text()
        if not text: return
        editor = self.get_editor()
        if not editor or isinstance(editor, QTextBrowser):
            return
        # findFirst(expr, re, cs, wo, wrap, forward=True, line=-1, index=-1)
        found = editor.findFirst(text, False, False, False, True, True)
        if not found:
            # Try from start if not found (wrap)
            editor.findFirst(text, False, False, False, True, True, 0, 0)

    def on_find_prev(self):
        text = self.search_input.text()
        if not text: return
        editor = self.get_editor()
        if not editor or isinstance(editor, QTextBrowser):
            return
        # To find previous, we use findFirst with forward=False
        editor.findFirst(text, False, False, False, True, False)

    def on_replace(self):
        replace_text = self.replace_input.text()
        editor = self.get_editor()
        if not editor or isinstance(editor, QTextBrowser):
            return
        if editor.hasSelectedText():
            editor.replace(replace_text)
            self.on_find_next()
        else:
            self.on_find_next()

    def on_replace_all(self):
        search_text = self.search_input.text()
        replace_text = self.replace_input.text()
        if not search_text: return
        
        editor = self.get_editor()
        if not editor or isinstance(editor, QTextBrowser):
            return
        
        editor.beginUndoAction()
        found = editor.findFirst(search_text, False, False, False, True, True, 0, 0)
        while found:
            editor.replace(replace_text)
            found = editor.findNext()
        editor.endUndoAction()

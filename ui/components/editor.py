from PyQt6.Qsci import QsciScintilla, QsciLexerPython, QsciAPIs
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt

class TMLLexer(QsciLexerPython):
    """
    Custom Lexer for TML based on Python lexer.
    Forces specific keywords to be highlighted by injecting them into the keyword list.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        
    def keywords(self, set_idx):
        # Set 1 is the standard keyword set for Python lexer (Control Flow)
        if set_idx == 1:
            python_keywords = super().keywords(1) or ""
            tml_control = "let func set if else while break return function async await try catch finally"
            return f"{python_keywords} {tml_control}"
        
        # Set 2 is for Built-ins/Modules in QsciLexerPython (usually highlighted differently)
        if set_idx == 2:
            # We use this for modules and core objects
            tml_modules = "keyboard mouse time math random window screen system net tick macro Vector"
            return tml_modules
            
        return super().keywords(set_idx)

class TMLScintilla(QsciScintilla):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_editor()
        self.setup_autocomplete()

    def setup_editor(self):
        # Font
        font = QFont("Consolas", 12)
        self.setFont(font)
        self.setMarginsFont(font)

        # Auto-pairing
        self.SendScintilla(QsciScintilla.SCI_SETAUTOMATICFOLD, 0x04) # SCI_AUTOMATICFOLD_CHANGE
        
        # Theme (Monokai-inspired)
        self.setCaretForegroundColor(QColor("#f8f8f2"))
        self.setCaretLineVisible(True)
        self.setCaretLineBackgroundColor(QColor("#3e3d32"))
        
        # Line numbers
        self.setMarginType(0, QsciScintilla.MarginType.NumberMargin)
        self.setMarginWidth(0, "0000")
        self.setMarginsBackgroundColor(QColor("#272822"))
        self.setMarginsForegroundColor(QColor("#90908a"))
        self.setMarginLineNumbers(0, True)

        # Indentation
        self.setIndentationsUseTabs(False)
        self.setIndentationWidth(4)
        self.setTabWidth(4)
        self.setIndentationGuides(True)
        self.setIndentationGuidesBackgroundColor(QColor("#49483e"))
        self.setIndentationGuidesForegroundColor(QColor("#49483e"))
        self.setAutoIndent(True)

        # Selection
        self.setSelectionBackgroundColor(QColor("#49483e"))
        self.setSelectionForegroundColor(QColor("#f8f8f2"))

        # Lexer (Customized TML Lexer)
        self.lexer = TMLLexer(self)
        self.lexer.setDefaultFont(font)
        self.lexer.setDefaultPaper(QColor("#272822"))
        self.lexer.setDefaultColor(QColor("#f8f8f2"))
        
        # Monokai Palette
        self.lexer.setColor(QColor("#f92672"), QsciLexerPython.Keyword) 
        self.lexer.setColor(QColor("#66d9ef"), 14)
        self.lexer.setColor(QColor("#66d9ef"), QsciLexerPython.ClassName)
        self.lexer.setColor(QColor("#a6e22e"), QsciLexerPython.FunctionMethodName)
        self.lexer.setColor(QColor("#e6db74"), QsciLexerPython.DoubleQuotedString)
        self.lexer.setColor(QColor("#e6db74"), QsciLexerPython.SingleQuotedString)
        self.lexer.setColor(QColor("#75715e"), QsciLexerPython.Comment)
        self.lexer.setColor(QColor("#ae81ff"), QsciLexerPython.Number)
        self.lexer.setColor(QColor("#f92672"), QsciLexerPython.Operator)
        self.lexer.setColor(QColor("#fd971f"), QsciLexerPython.Identifier)
        
        # Brace matching
        self.setBraceMatching(QsciScintilla.BraceMatch.SloppyBraceMatch)
        self.setUnmatchedBraceBackgroundColor(QColor("#f92672"))
        self.setMatchedBraceBackgroundColor(QColor("#3e3d32"))
        self.setMatchedBraceForegroundColor(QColor("#a6e22e"))
        
        # Execution marker
        self.markerDefine(QsciScintilla.MarkerSymbol.Background, 1)
        self.setMarkerBackgroundColor(QColor("#3e3d32"), 1)
        
        # Code Folding
        self.setFolding(QsciScintilla.FoldStyle.BoxedTreeFoldStyle)
        self.setFoldMarginColors(QColor("#272822"), QColor("#272822"))
        
        self.setLexer(self.lexer)
        self.setUtf8(True)
        self.setWrapMode(QsciScintilla.WrapMode.WrapWord)
        self.setWrapVisualFlags(QsciScintilla.WrapVisualFlag.WrapFlagByText)

    def setup_autocomplete(self):
        self.api = QsciAPIs(self.lexer)
        keywords = ["if", "else", "while", "break", "return", "function", "async", "await", "try", "catch", "finally", "let", "func", "set"]
        for k in keywords: self.api.add(k)
        
        modules = ["keyboard", "mouse", "time", "math", "random", "window", "screen", "system", "net", "tick", "macro", "sound", "storage", "ui"]
        for m in modules: self.api.add(m)
        
        tml_api = [
            "math.sin", "math.cos", "math.tan", "math.sqrt", "math.abs", "math.floor", 
            "math.ceil", "math.round", "math.pow", "math.log", "math.vector", "math.lerp",
            "math.bezier", "math.bezier3", "math.jitter", "math.pi", "math.e",
            "random.random", "random.uniform", "random.randint", "random.choice", "random.shuffle",
            "screen.size", "screen.get_color", "screen.find_image", "screen.find_all_images",
            "screen.find_color", "screen.wait_for_color", "screen.set_brightness", "screen.monitor_on", "screen.monitor_off",
            "time.sleep", "time.time", "time.time_str", "time.time_ms", "time.perfcount",
            "system.set_clipboard", "system.get_clipboard", "system.alert", "system.set_keyboard_layout", "system.get_keyboard_layout",
            "net.post", "net.get", "net.discord_webhook",
            "mouse.click", "mouse.move", "mouse.move_rel", "mouse.press", "mouse.release", "mouse.scroll", "mouse.position", "mouse.x", "mouse.y", "mouse.pos", "mouse.is_pressed", "mouse.double_click", "mouse.smooth_move", "mouse.smooth_move_rel", "mouse.move_bezier",
            "keyboard.type", "keyboard.press", "keyboard.release", "keyboard.tap", "keyboard.hotkey", "keyboard.is_pressed",
            "sound.set_volume", "sound.get_volume",
            "storage.write", "storage.read", "storage.has", "storage.delete", "storage.clear", "storage.set_config", "storage.save",
            "ui.set_text", "ui.set_template", "ui.show", "ui.hide", "ui.move", "ui.set_size", "ui.set_font_size", "ui.set_scale", "ui.set_color", "ui.set_bg_opacity", "ui.anchor", "ui.clear",
            "macro.active", "macro.exit", "macro.run", "macro.stop", "macro.is_running",
            "print", "exit", "Vector", "None", "left", "right", "middle",
            "K_A", "K_B", "K_C", "K_D", "K_E", "K_F", "K_G", "K_H", "K_I", "K_J", 
            "K_K", "K_L", "K_M", "K_N", "K_O", "K_P", "K_Q", "K_R", "K_S", "K_T", 
            "K_U", "K_V", "K_W", "K_X", "K_Y", "K_Z",
            "K_0", "K_1", "K_2", "K_3", "K_4", "K_5", "K_6", "K_7", "K_8", "K_9",
            "K_F1", "K_F2", "K_F3", "K_F4", "K_F5", "K_F6", "K_F7", "K_F8", "K_F9", "K_F10", "K_F11", "K_F12",
            "K_ENTER", "K_ESC", "K_SPACE", "K_TAB", "K_BACKSPACE", "K_DELETE", "K_INSERT",
            "K_HOME", "K_END", "K_PAGE_UP", "K_PAGE_DOWN", "K_UP", "K_DOWN", "K_LEFT", "K_RIGHT",
            "K_SHIFT", "K_CTRL", "K_ALT", "K_CAPS_LOCK", "tick.delta"
        ]
        for item in tml_api: self.api.add(item)
        for item in tml_api: self.api.add(item)
        self.api.prepare()
        
        self.setAutoCompletionThreshold(1)
        self.setAutoCompletionSource(QsciScintilla.AutoCompletionSource.AcsAll)
        self.setAutoCompletionCaseSensitivity(False)
        self.setAutoCompletionReplaceWord(True)

    def keyPressEvent(self, event):
        char = event.text()
        pairs = {'(': ')', '[': ']', '{': '}', '"': '"', "'": "'"}
        
        if char in pairs:
            line, index = self.getCursorPosition()
            if self.hasSelectedText():
                line_from, index_from, line_to, index_to = self.getSelection()
                selected_text = self.selectedText()
                self.replace(f"{char}{selected_text}{pairs[char]}")
                self.setSelection(line_from, index_from, line_to, index_to + 2 if line_from == line_to else index_to)
                return
            else:
                super().keyPressEvent(event)
                self.insert(pairs[char])
                self.setCursorPosition(line, index + 1)
                return
        
        if char in [')', ']', '}', '"', "'"]:
            line, index = self.getCursorPosition()
            if index < self.lineLength(line):
                next_char = self.text(line)[index]
                if next_char == char:
                    self.setCursorPosition(line, index + 1)
                    return

        super().keyPressEvent(event)

    def toggle_comment(self):
        if not self.hasSelectedText():
            line, index = self.getCursorPosition()
            text = self.text(line)
            if text.strip().startswith("#"):
                # Uncomment
                new_text = text.replace("#", "", 1)
                self.setSelection(line, 0, line, len(text))
                self.replace(new_text)
                self.setCursorPosition(line, max(0, index - 1))
            else:
                # Comment
                self.insertAt("#", line, 0)
                self.setCursorPosition(line, index + 1)
        else:
            line_from, index_from, line_to, index_to = self.getSelection()
            # If nothing is selected on the last line, don't comment it
            if index_to == 0 and line_to > line_from:
                line_to -= 1
            
            self.beginUndoAction()
            for line in range(line_from, line_to + 1):
                text = self.text(line)
                if text.strip().startswith("#"):
                    new_text = text.replace("#", "", 1)
                    self.setSelection(line, 0, line, len(text))
                    self.replace(new_text)
                else:
                    self.insertAt("#", line, 0)
            self.endUndoAction()

    def duplicate_line(self):
        line, index = self.getCursorPosition()
        text = self.text(line)
        if not text.endswith("\n"):
            text += "\n"
        self.insertAt(text, line + 1, 0)
        self.setCursorPosition(line + 1, index)

    def move_line_up(self):
        line, index = self.getCursorPosition()
        if line == 0: return
        
        text = self.text(line)
        self.beginUndoAction()
        self.setSelection(line, 0, line, self.lineLength(line))
        self.removeSelectedText()
        self.insertAt(text, line - 1, 0)
        self.setCursorPosition(line - 1, index)
        self.endUndoAction()

    def move_line_down(self):
        line, index = self.getCursorPosition()
        if line == self.lines() - 1: return
        
        text = self.text(line)
        self.beginUndoAction()
        self.setSelection(line, 0, line, self.lineLength(line))
        self.removeSelectedText()
        self.insertAt(text, line + 1, 0)
        self.setCursorPosition(line + 1, index)
        self.endUndoAction()

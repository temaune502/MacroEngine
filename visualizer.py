import sys
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QGraphicsView, QGraphicsScene, 
                             QGraphicsRectItem, QGraphicsTextItem, QGraphicsLineItem,
                             QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QFileDialog,
                             QScrollArea, QFrame, QListWidget, QListWidgetItem, QSplitter, QLabel)
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QPen, QBrush, QColor, QFont, QPainter

from compiler.opcodes import OpCode
from compiler.compiler import Compiler
from compiler.base import Chunk, FunctionObject
from compiler.parser import Parser
from compiler.lexer import Lexer

class Block:
    def __init__(self, start_ip, end_ip, instructions):
        self.start_ip = start_ip
        self.end_ip = end_ip
        self.instructions = instructions
        self.successors = []
        self.x = 0
        self.y = 0
        self.width = 0
        self.height = 0
        self.type = "normal" # normal, entry, exit, loop_header

class FlowAnalyzer:
    def analyze(self, chunk: Chunk):
        code = chunk.code
        if not code:
            return []

        # Find all entry points (jump targets)
        entry_points = {0}
        jump_targets = set()
        for i, (op, arg) in enumerate(code):
            if op in (OpCode.JUMP, OpCode.JUMP_IF_FALSE, OpCode.JUMP_IF_TRUE, 
                      OpCode.JUMP_IF_FALSE_POP, OpCode.JUMP_IF_TRUE_POP, OpCode.LOOP, OpCode.FOR_ITER):
                if arg is not None:
                    entry_points.add(arg)
                    jump_targets.add(arg)
                entry_points.add(i + 1)

        # Create blocks
        blocks = []
        sorted_entries = sorted([e for e in entry_points if e <= len(code)])
        for i in range(len(sorted_entries)):
            start = sorted_entries[i]
            if start >= len(code):
                continue
            end = sorted_entries[i+1] if i+1 < len(sorted_entries) else len(code)
            
            block_code = code[start:end]
            b = Block(start, end, block_code)
            if start == 0:
                b.type = "entry"
            elif any(op in (OpCode.RETURN, OpCode.RETURN_NONE) for op, _ in block_code):
                b.type = "exit"
            elif start in jump_targets:
                # Check if it's a loop header (target of a LOOP instruction)
                is_loop = False
                for op, arg in code:
                    if op == OpCode.LOOP and arg == start:
                        is_loop = True
                        break
                if is_loop:
                    b.type = "loop_header"
            
            blocks.append(b)

        # Connect blocks
        block_map = {b.start_ip: b for b in blocks}
        for b in blocks:
            if not b.instructions: continue
            last_op, last_arg = b.instructions[-1]
            
            if last_op in (OpCode.JUMP, OpCode.LOOP):
                if last_arg in block_map:
                    b.successors.append(block_map[last_arg])
            elif last_op in (OpCode.JUMP_IF_FALSE, OpCode.JUMP_IF_TRUE, 
                            OpCode.JUMP_IF_FALSE_POP, OpCode.JUMP_IF_TRUE_POP, OpCode.FOR_ITER):
                # Conditional jump: can go to target or next block
                if last_arg in block_map:
                    b.successors.append(block_map[last_arg])
                if b.end_ip in block_map:
                    b.successors.append(block_map[b.end_ip])
            elif last_op not in (OpCode.RETURN, OpCode.RETURN_NONE):
                # Fall through to next block
                if b.end_ip in block_map:
                    b.successors.append(block_map[b.end_ip])
        
        return blocks

class BlockItem(QGraphicsRectItem):
    def __init__(self, block, on_move_callback):
        super().__init__(0, 0, block.width, block.height)
        self.block = block
        self.on_move_callback = on_move_callback
        
        # Color based on type
        bg_color = QColor(245, 245, 245)
        if block.type == "entry": bg_color = QColor(200, 255, 200)
        elif block.type == "exit": bg_color = QColor(255, 200, 200)
        elif block.type == "loop_header": bg_color = QColor(200, 200, 255)
        
        self.setBrush(QBrush(bg_color))
        self.setPen(QPen(Qt.black, 1))
        
        self.setFlag(QGraphicsRectItem.ItemIsMovable)
        self.setFlag(QGraphicsRectItem.ItemIsSelectable)
        self.setFlag(QGraphicsRectItem.ItemSendsGeometryChanges)
        
        # Add text
        text_lines = [f"--- Block {block.start_ip} ---"]
        for ip, (op, arg) in enumerate(block.instructions):
            actual_ip = block.start_ip + ip
            arg_str = f" {arg}" if arg is not None else ""
            text_lines.append(f"{actual_ip:03d}: {op.name}{arg_str}")
        
        self.text_item = QGraphicsTextItem("\n".join(text_lines), self)
        self.text_item.setFont(QFont("Consolas", 10))
        self.text_item.setDefaultTextColor(Qt.black)
        self.text_item.setPos(15, 15)
        
        self.setPos(block.x, block.y)

    def itemChange(self, change, value):
        if change == QGraphicsRectItem.ItemPositionChange:
            self.block.x = value.x()
            self.block.y = value.y()
            self.on_move_callback()
        return super().itemChange(change, value)

class FlowChartWidget(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.RubberBandDrag) # Better for selecting/moving
        self.blocks = []
        self.block_items = []
        self.edge_items = []
        
    def draw_blocks(self, blocks):
        self.scene.clear()
        self.block_items = []
        self.edge_items = []
        self.blocks = blocks
        if not blocks:
            return

        # 1. Assign levels to blocks using BFS (handling disconnected components)
        levels = {} # level -> list of blocks
        block_to_level = {}
        visited = set()
        
        def assign_levels_from(start_block, start_level):
            queue = [(start_block, start_level)]
            while queue:
                b, level = queue.pop(0)
                if b.start_ip in visited:
                    if block_to_level[b.start_ip] < level:
                        if b in levels.get(block_to_level[b.start_ip], []):
                            levels[block_to_level[b.start_ip]].remove(b)
                        block_to_level[b.start_ip] = level
                        if level not in levels: levels[level] = []
                        levels[level].append(b)
                    continue
                
                visited.add(b.start_ip)
                block_to_level[b.start_ip] = level
                if level not in levels: levels[level] = []
                levels[level].append(b)
                
                for succ in b.successors:
                    if succ.start_ip > b.start_ip:
                        queue.append((succ, level + 1))

        # First pass from entry
        if blocks:
            assign_levels_from(blocks[0], 0)
            
        # Handle unreachable blocks
        for b in blocks:
            if b.start_ip not in visited:
                max_l = max(levels.keys()) + 1 if levels else 0
                assign_levels_from(b, max_l)

        # 2. Position blocks based on levels
        max_level = max(levels.keys()) if levels else 0
        curr_y = 50
        
        # Calculate horizontal spacing
        level_widths = {}
        for level, level_blocks in levels.items():
            # Initial sizes to calculate total width of the level
            for b in level_blocks:
                text_lines = [f"--- Block {b.start_ip} ---"]
                for ip, (op, arg) in enumerate(b.instructions):
                    actual_ip = b.start_ip + ip
                    arg_str = f" {arg}" if arg is not None else ""
                    text_lines.append(f"{actual_ip:03d}: {op.name}{arg_str}")
                
                text_item = QGraphicsTextItem("\n".join(text_lines))
                text_item.setFont(QFont("Consolas", 10))
                rect = text_item.boundingRect()
                b.width, b.height = rect.width() + 30, rect.height() + 30

            level_widths[level] = sum(b.width for b in level_blocks) + (len(level_blocks) - 1) * 100

        max_width = max(level_widths.values()) if level_widths else 800
        
        for level in range(max_level + 1):
            if level not in levels: continue
            
            level_blocks = levels[level]
            total_level_width = level_widths[level]
            curr_x = (max_width - total_level_width) / 2 + 100
            
            max_h_in_level = 0
            for b in level_blocks:
                b.x, b.y = curr_x, curr_y
                
                item = BlockItem(b, self.update_edges)
                self.scene.addItem(item)
                self.block_items.append(item)
                
                curr_x += b.width + 100
                max_h_in_level = max(max_h_in_level, b.height)
            
            curr_y += max_h_in_level + 100

        self.update_edges()

    def update_edges(self):
        # Remove old edges
        for item in self.edge_items:
            self.scene.removeItem(item)
        self.edge_items = []

        for b in self.blocks:
            for i, succ in enumerate(b.successors):
                color = Qt.blue
                if len(b.successors) > 1:
                    color = Qt.red if i == 0 else Qt.darkGreen
                
                from PySide6.QtGui import QPainterPath
                path = QPainterPath()
                
                # Orthogonal lines logic
                if succ.y >= b.y + b.height: # Downward
                    start_p = QPointF(b.x + b.width / 2, b.y + b.height)
                    end_p = QPointF(succ.x + succ.width / 2, succ.y)
                    
                    mid_y = start_p.y() + (end_p.y() - start_p.y()) / 2
                    path.moveTo(start_p)
                    path.lineTo(start_p.x(), mid_y)
                    path.lineTo(end_p.x(), mid_y)
                    path.lineTo(end_p)
                elif succ.start_ip <= b.start_ip: # Loop back (to the left)
                    start_p = QPointF(b.x, b.y + b.height / 2)
                    end_p = QPointF(succ.x, succ.y + succ.height / 2)
                    
                    nest_off = 40 + (b.start_ip % 5) * 20
                    path.moveTo(start_p)
                    path.lineTo(b.x - nest_off, start_p.y())
                    path.lineTo(b.x - nest_off, end_p.y())
                    path.lineTo(end_p)
                else: # Forward but not directly below
                    start_p = QPointF(b.x + b.width, b.y + b.height / 2)
                    end_p = QPointF(succ.x, succ.y + succ.height / 2)
                    
                    mid_x = start_p.x() + (end_p.x() - start_p.x()) / 2
                    path.moveTo(start_p)
                    path.lineTo(mid_x, start_p.y())
                    path.lineTo(mid_x, end_p.y())
                    path.lineTo(end_p)

                pen = QPen(color, 2)
                if succ.start_ip <= b.start_ip:
                    pen.setStyle(Qt.DashLine)
                
                edge = self.scene.addPath(path, pen)
                self.edge_items.append(edge)
                
                # Draw arrowhead
                # Find last segment for arrowhead angle
                points = []
                for j in range(path.elementCount()):
                    el = path.elementAt(j)
                    points.append(QPointF(el.x, el.y))
                
                if len(points) >= 2:
                    p_last = points[-1]
                    p_prev = points[-2]
                    self.draw_arrowhead(p_prev, p_last, color)

    def draw_arrowhead(self, start, end, color):
        arrow_size = 12
        import math
        dx = end.x() - start.x()
        dy = end.y() - start.y()
        angle = math.atan2(dy, dx)
        
        p1 = end - QPointF(math.cos(angle - math.pi/6) * arrow_size, 
                        math.sin(angle - math.pi/6) * arrow_size)
        p2 = end - QPointF(math.cos(angle + math.pi/6) * arrow_size, 
                        math.sin(angle + math.pi/6) * arrow_size)
        
        arrow = self.scene.addPolygon([end, p1, p2], QPen(color), QBrush(color))
        self.edge_items.append(arrow)

class VisualizerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Macro Language Execution Visualizer")
        self.resize(1200, 900)
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        
        # Top toolbar
        self.toolbar = QHBoxLayout()
        self.btn_open = QPushButton("📂 Open .tml File")
        self.btn_open.setStyleSheet("padding: 8px; font-weight: bold;")
        self.btn_open.clicked.connect(self.open_file)
        self.toolbar.addWidget(self.btn_open)
        self.toolbar.addStretch()
        self.layout.addLayout(self.toolbar)
        
        # Main splitter for sidebar and visualization
        self.splitter = QSplitter(Qt.Horizontal)
        
        # Sidebar for functions
        self.sidebar = QWidget()
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar_layout.addWidget(QLabel("<b>Functions & Modules</b>"))
        
        self.func_list = QListWidget()
        self.func_list.itemClicked.connect(self.on_func_selected)
        self.sidebar_layout.addWidget(self.func_list)
        
        self.splitter.addWidget(self.sidebar)
        
        # Main visualization area
        self.flow_chart = FlowChartWidget()
        self.splitter.addWidget(self.flow_chart)
        
        # Set splitter sizes (sidebar 250px, visualization rest)
        self.splitter.setSizes([250, 950])
        self.layout.addWidget(self.splitter)
        
        self.analyzer = FlowAnalyzer()
        self.current_compiler = None
        self.chunk_data = {} # name -> chunk

    def on_func_selected(self, item):
        name = item.text()
        if name in self.chunk_data:
            chunk = self.chunk_data[name]
            blocks = self.analyzer.analyze(chunk)
            self.flow_chart.draw_blocks(blocks)
            self.setWindowTitle(f"Visualizing: {name}")

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open TML File", "", "TML Files (*.tml)")
        if file_path:
            self.visualize(file_path)
            
    def visualize(self, file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()
            
        try:
            # Create a fresh compiler for each file
            self.current_compiler = Compiler()
            lexer = Lexer(source)
            tokens = lexer.tokenize()
            parser = Parser(tokens)
            statements = parser.parse()
            main_chunk = self.current_compiler.compile(statements)
            
            # Clear old data
            self.func_list.clear()
            self.chunk_data = {}
            
            # Add Main
            self.chunk_data["Main"] = main_chunk
            self.func_list.addItem("Main")
            
            # Add Functions
            for name, func_obj in self.current_compiler.functions.items():
                self.chunk_data[name] = func_obj.chunk
                self.func_list.addItem(name)
            
            # Select Main by default
            if self.func_list.count() > 0:
                self.func_list.setCurrentRow(0)
                self.on_func_selected(self.func_list.item(0))
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", f"Failed to compile or visualize:\n{str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VisualizerWindow()
    
    # If a file is passed as an argument, open it immediately
    if len(sys.argv) > 1:
        file_path = os.path.abspath(sys.argv[1])
        if os.path.exists(file_path):
            window.visualize(file_path)
            
    window.show()
    sys.exit(app.exec())

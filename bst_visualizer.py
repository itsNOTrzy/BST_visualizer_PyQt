# -*- coding: utf-8 -*-
from __future__ import annotations
import sys
import random
from dataclasses import dataclass
from typing import Optional, Dict, Tuple, List, Set

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QFontDatabase

# =============================
# 跨平台字体 & 样式
# =============================

# 平台与字体挑选
IS_WIN = sys.platform.startswith("win")

def _pick_win_yahei_family() -> str:
    db = QFontDatabase()
    for fam in ("Microsoft YaHei UI", "Microsoft YaHei"):  # UI 优先，适合小字号
        if fam in db.families():
            return fam
    return "Segoe UI"  #（极少见）

def _get_ui_font(point_size: int) -> QtGui.QFont:
    db = QFontDatabase()
    if IS_WIN:
        family = _pick_win_yahei_family()  # Windows 用微软雅黑
    else:
        preferred = [
            "PingFang SC", "Hiragino Sans GB", "Noto Sans CJK SC",
            "Microsoft YaHei", "Segoe UI", "Arial", "Helvetica", "Sans Serif",
        ]
        family = next((f for f in preferred if f in db.families()), QtGui.QFont().defaultFamily())

    font = QtGui.QFont(family, point_size)
    font.setBold(True)   # 保持原来的视觉风格（若嫌 Win 变胖，可改为 DemiBold）
    return font

BTN_STYLE = {
    'primary': ("#1e88e5", "#1565c0"),   # 蓝
    'success': ("#43a047", "#2e7d32"),   # 绿
    'warning': ("#f9a825", "#f57f17"),   # 黄
    'danger':  ("#e53935", "#c62828"),   # 红
    'secondary': ("#90a4ae", "#607d8b"), # 灰
}

def style_button(btn: QtWidgets.QPushButton, variant: str = 'primary'):
    base, hover = BTN_STYLE.get(variant, BTN_STYLE['primary'])
    btn.setStyleSheet(f"""
        QPushButton {{
            background-color: {base}; color: white; border: none; border-radius: 10px;
            padding: 8px 16px; font-weight: 600; }}
        QPushButton:hover {{ background-color: {hover}; }}
        QPushButton:pressed {{ transform: scale(0.99); }}
        QPushButton:disabled {{ background-color: #cfd8dc; color: #eceff1; }}
    """)

def style_groupbox(gb: QtWidgets.QGroupBox):
    gb.setStyleSheet("""
        QGroupBox { border: 2px solid #1e88e5; border-radius: 8px; margin-top: 8px; }
        QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 4px; color: #1e88e5; font-weight: 600; }
    """)

def style_frame(frame: QtWidgets.QFrame):
    frame.setStyleSheet("QFrame { border: 2px solid #90caf9; border-radius: 8px; background: #ffffff; }")

# =============================
# 模型：二叉排序树（BST）
# =============================

@dataclass(eq=False)
class BSTNode:
    key: int
    left: Optional['BSTNode'] = None
    right: Optional['BSTNode'] = None
    parent: Optional['BSTNode'] = None

    def is_left_child(self) -> bool:
        return self.parent is not None and self.parent.left is self

    def is_right_child(self) -> bool:
        return self.parent is not None and self.parent.right is self

class BST:
    def __init__(self):
        self.root: Optional[BSTNode] = None

    def insert(self, key: int) -> Tuple[Optional[BSTNode], Optional[BSTNode]]:
        y = None
        x = self.root
        while x is not None:
            y = x
            if key == x.key:
                return None, x  # 重复
            x = x.left if key < x.key else x.right
        z = BSTNode(key=key, parent=y)
        if y is None:
            self.root = z
        elif key < y.key:
            y.left = z
        else:
            y.right = z
        return z, y

    def search(self, key: int) -> Tuple[List[BSTNode], Optional[BSTNode]]:
        path: List[BSTNode] = []
        x = self.root
        while x is not None:
            path.append(x)
            if key == x.key:
                return path, x
            x = x.left if key < x.key else x.right
        return path, None

    def minimum(self, x: BSTNode) -> BSTNode:
        while x.left is not None:
            x = x.left
        return x

    def transplant(self, u: BSTNode, v: Optional[BSTNode]):
        if u.parent is None:
            self.root = v
        elif u.is_left_child():
            u.parent.left = v
        else:
            u.parent.right = v
        if v is not None:
            v.parent = u.parent

    def delete(self, key: int) -> Optional[BSTNode]:
        _, z = self.search(key)
        if z is None:
            return None
        if z.left is None:
            self.transplant(z, z.right)
        elif z.right is None:
            self.transplant(z, z.left)
        else:
            y = self.minimum(z.right)
            if y.parent is not z:
                self.transplant(y, y.right)
                y.right = z.right
                if y.right: y.right.parent = y
            self.transplant(z, y)
            y.left = z.left
            if y.left: y.left.parent = y
        return z

    def inorder(self) -> List[int]:
        res: List[int] = []
        def dfs(n: Optional[BSTNode]):
            if not n: return
            dfs(n.left); res.append(n.key); dfs(n.right)
        dfs(self.root)
        return res

    def nodes(self) -> List[BSTNode]:
        out: List[BSTNode] = []
        def dfs(n: Optional[BSTNode]):
            if not n: return
            dfs(n.left); out.append(n); dfs(n.right)
        dfs(self.root)
        return out

    def depth(self) -> int:
        def h(n: Optional[BSTNode]) -> int:
            return 0 if not n else 1 + max(h(n.left), h(n.right))
        return h(self.root)

    def clear(self):
        self.root = None

# =============================
# 图形项：边与节点
# =============================

# 自适应画布的 QGraphicsView
class AdaptiveGraphicsView(QtWidgets.QGraphicsView):
    resized = QtCore.pyqtSignal()  # 画布尺寸改变信号

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        super().resizeEvent(event)
        # 将场景矩形同步为当前可见区域大小
        if self.scene() is not None:
            r = QtCore.QRectF(0, 0, self.viewport().width(), self.viewport().height())
            self.scene().setSceneRect(r)
        self.resized.emit()

class EdgeItem(QtWidgets.QGraphicsPathItem):
    def __init__(self, parent_pos: QtCore.QPointF, child_pos: QtCore.QPointF, r: float):
        super().__init__()
        self.setZValue(-1)
        pen = QtGui.QPen(QtCore.Qt.black)
        pen.setWidthF(1.5)
        self.setPen(pen)
        self.r = r
        self.update_path(parent_pos, child_pos)

    def update_path(self, p: QtCore.QPointF, c: QtCore.QPointF):
        v = QtCore.QPointF(c.x() - p.x(), c.y() - p.y())
        dist = max(1e-6, (v.x()**2 + v.y()**2)**0.5)
        ux, uy = v.x()/dist, v.y()/dist
        start = QtCore.QPointF(p.x() + ux*self.r, p.y() + uy*self.r)
        end   = QtCore.QPointF(c.x() - ux*self.r, c.y() - uy*self.r)
        path = QtGui.QPainterPath(start)
        path.lineTo(end)
        ah, aw = self.r*0.6, self.r*0.5
        left  = QtCore.QPointF(end.x()-ux*ah-uy*aw, end.y()-uy*ah+ux*aw)
        right = QtCore.QPointF(end.x()-ux*ah+uy*aw, end.y()-uy*ah-ux*aw)
        path.moveTo(end); path.lineTo(left)
        path.moveTo(end); path.lineTo(right)
        self.setPath(path)

class NodeItem(QtWidgets.QGraphicsItemGroup):
    # 统一的配色（可按需微调）
    _C_STROKE = QtGui.QColor("#2559a5")  # 边
    _C_FILL   = QtGui.QColor("#d0deed")  # 填充
    _C_FILL_HL= QtGui.QColor("#6686D7")  # 高亮

    def __init__(self, key: int, radius: float = 22.0):
        super().__init__()
        self.key = key
        self.radius = radius
        self.on_click = None  # 可注入回调

        # 圆形：浅蓝填充 + 蓝色描边（加粗一点更清晰）
        self.circle = QtWidgets.QGraphicsEllipseItem(-radius, -radius, 2*radius, 2*radius)
        self.circle.setBrush(QtGui.QBrush(self._C_FILL))
        pen = QtGui.QPen(self._C_STROKE)
        pen.setWidthF(3.0)
        self.circle.setPen(pen)

        # 文本
        self.text = QtWidgets.QGraphicsSimpleTextItem(str(key))
        # 先给一个占位字体（只决定字形/家族，不锁定字号）
        self.text.setFont(_get_ui_font(10))  # 字体家族复用你原来的选择
        self._fit_text_to_radius()           # 自适应字号并居中

        # 分组
        self.addToGroup(self.circle)
        self.addToGroup(self.text)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
        self.setZValue(1)

    def _fit_text_to_radius(self):
        """
        根据当前 self.radius，利用像素字号 + QFontMetricsF 进行二分拟合，
        保证文字在圆内留有适当边距（平台/DPI 无关，跨平台一致）。
        """
        d = 2.0 * self.radius
        # 预留一点边距，避免碰圆边（0.70～0.80）
        max_w = max_h = d * 0.72

        # 保持家族一致（不要用粗体，粗体在 Windows 会显得更“大”）
        fam = _pick_win_yahei_family() if IS_WIN else self.text.font().family()

        lo, hi = 6, int(self.radius * 2.2)  # 像素字号搜索范围
        best = lo
        best_font = None

        while lo <= hi:
            mid = (lo + hi) // 2
            f = QtGui.QFont(fam)
            f.setPixelSize(mid)                   # 核心：像素字号，摆脱点字号与平台缩放差异
            f.setWeight(QtGui.QFont.DemiBold)     # 比 setBold(True) 温和，跨平台外观更稳定
            fm = QtGui.QFontMetricsF(f)
            br = fm.tightBoundingRect(str(self.key))

            if br.width() <= max_w and br.height() <= max_h:
                best = mid
                best_font = f
                lo = mid + 1
            else:
                hi = mid - 1

        if best_font is None:
            best_font = QtGui.QFont(fam)
            best_font.setPixelSize(best)
            best_font.setWeight(QtGui.QFont.DemiBold)

        self.text.setFont(best_font)
        # 重新测量后居中
        br = self.text.boundingRect()
        self.text.setPos(-br.width()/2.0, -br.height()/2.0)

    def set_radius(self, r: float):
        self.radius = r
        self.circle.setRect(-r, -r, 2*r, 2*r)
        self._fit_text_to_radius()  # 改半径时重新拟合字体与位置

    def highlight(self, on: bool):
        # 高亮改成更深一点的浅蓝，关闭则恢复浅蓝
        self.circle.setBrush(QtGui.QBrush(self._C_FILL_HL if on else self._C_FILL))

    def mousePressEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        if callable(self.on_click):
            self.on_click(self.key)
        super().mousePressEvent(event)

# =============================
# 视图：BSTVisualizer
# =============================

class BSTVisualizer(QtWidgets.QMainWindow):
    SCENE_W = 850
    SCENE_H = 600

    def __init__(self):
        super().__init__()
        self.setWindowTitle("二叉排序树可视化")
        self.resize(1150, 756)
        self.bst = BST()

        # 画布
        self.scene = QtWidgets.QGraphicsScene(0, 0, self.SCENE_W, self.SCENE_H)
        self.view = AdaptiveGraphicsView(self.scene)
        self.view.setRenderHint(QtGui.QPainter.Antialiasing, True)
        self.view.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(245, 247, 250)))
        self.view.setViewportUpdateMode(QtWidgets.QGraphicsView.FullViewportUpdate)
        self.view.setFrameShape(QtWidgets.QFrame.NoFrame)  # 去除额外边框
        self.view.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        # 顶部控制
        self.input_edit = QtWidgets.QLineEdit()
        self.input_edit.setPlaceholderText("输入数字，可用空格/逗号分隔：8 3 10 1 6 14 4 7 13")
        self.btn_insert = QtWidgets.QPushButton("插入/创建")
        self.btn_search = QtWidgets.QPushButton("查找")
        self.btn_delete = QtWidgets.QPushButton("删除")
        self.btn_clear  = QtWidgets.QPushButton("清空")
        self.btn_random = QtWidgets.QPushButton("随机生成")
        for btn, var in [
            (self.btn_insert,'primary'), (self.btn_search,'secondary'),
            (self.btn_delete,'danger'),  (self.btn_clear,'warning'), (self.btn_random,'secondary')
        ]:
            style_button(btn, var)

        self.spin_random = QtWidgets.QSpinBox(); self.spin_random.setRange(1, 1000); self.spin_random.setValue(10)
        
        # 速度滑尺：10% ~ 400%（即 0.1x ~ 4.0x）
        self.speed_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.speed_slider.setRange(10, 400)
        self.speed_slider.setValue(100)  # 100% = 1.0x
        # 动画基准（不动的“基准时长”，真正用时会除以速度倍率）
        self.base_anim_ms = 450
        self.speed_mult = 1.0
        self.chk_anim = QtWidgets.QCheckBox("动画开关"); self.chk_anim.setChecked(True)

        gb_control = QtWidgets.QGroupBox("控制面板"); style_groupbox(gb_control)
        grid = QtWidgets.QGridLayout(gb_control)
        grid.addWidget(QtWidgets.QLabel("输入数据："), 0, 0)
        grid.addWidget(self.input_edit, 0, 1, 1, 4)
        grid.addWidget(self.btn_insert, 0, 5)
        grid.addWidget(QtWidgets.QLabel("随机数量："), 1, 0)
        grid.addWidget(self.spin_random, 1, 1)
        grid.addWidget(self.btn_random, 1, 2)
        grid.addWidget(self.btn_search, 1, 3)
        grid.addWidget(self.btn_delete, 1, 4)
        grid.addWidget(self.btn_clear, 1, 5)
        grid.addWidget(QtWidgets.QLabel("动画速度："), 2, 0)
        grid.addWidget(self.speed_slider, 2, 1, 1, 4)
        grid.addWidget(self.chk_anim, 2, 5)

        # 左视图框
        gb_view = QtWidgets.QGroupBox("可视化"); style_groupbox(gb_view)
        v_view = QtWidgets.QVBoxLayout(gb_view)
        frame_canvas = QtWidgets.QFrame(); style_frame(frame_canvas)
        lay_canvas = QtWidgets.QVBoxLayout(frame_canvas)
        lay_canvas.setContentsMargins(0, 0, 0, 0)  # 让画布完全贴合
        lay_canvas.addWidget(self.view)
        v_view.addWidget(frame_canvas)

        # 右信息面板
        gb_info = QtWidgets.QGroupBox("信息显示"); style_groupbox(gb_info)
        v_info = QtWidgets.QVBoxLayout(gb_info)
        self.info_state = QtWidgets.QTextEdit(); self.info_state.setReadOnly(True); self.info_state.setMinimumWidth(260)
        self.info_last  = QtWidgets.QTextEdit(); self.info_last.setReadOnly(True)
        self.info_selected = QtWidgets.QTextEdit(); self.info_selected.setReadOnly(True)
        sub1 = QtWidgets.QGroupBox("树状态"); style_groupbox(sub1); l1 = QtWidgets.QVBoxLayout(sub1); l1.addWidget(self.info_state)
        sub2 = QtWidgets.QGroupBox("最近操作"); style_groupbox(sub2); l2 = QtWidgets.QVBoxLayout(sub2); l2.addWidget(self.info_last)
        sub3 = QtWidgets.QGroupBox("选中节点"); style_groupbox(sub3); l3 = QtWidgets.QVBoxLayout(sub3); l3.addWidget(self.info_selected)
        v_info.addWidget(sub1); v_info.addWidget(sub2); v_info.addWidget(sub3); v_info.addStretch(1)

        # 底部状态栏
        self.status = QtWidgets.QLabel("就绪")
        status_frame = QtWidgets.QFrame(); status_layout = QtWidgets.QHBoxLayout(status_frame)
        status_layout.setContentsMargins(8,4,8,4); status_layout.addWidget(self.status)

        # 主布局
        top = QtWidgets.QWidget(); self.setCentralWidget(top)
        main_v = QtWidgets.QVBoxLayout(top)
        main_v.addWidget(gb_control)
        mid = QtWidgets.QHBoxLayout(); mid.addWidget(gb_view, 1); mid.addWidget(gb_info)
        main_v.addLayout(mid, 1)
        main_v.addWidget(status_frame)

        # 信号
        self.btn_insert.clicked.connect(self.on_insert_clicked)
        self.btn_search.clicked.connect(self.on_search_clicked)
        self.btn_delete.clicked.connect(self.on_delete_clicked)
        self.btn_clear.clicked.connect(self.on_clear_clicked)
        self.btn_random.clicked.connect(self.on_random_clicked)
        self.speed_slider.valueChanged.connect(self.on_speed_changed)

        # 状态
        self.node_item: Dict[BSTNode, NodeItem] = {}
        self.edge_items: List[EdgeItem] = []
        self.margin = 40
        self.animations: List[QtCore.QVariantAnimation] = []
        self.update_info_panels("初始化完成")

        # 画布尺寸变化 -> 节流重布局
        self._resize_timer = QtCore.QTimer(self)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.setInterval(80)  # 轻量节流，避免频繁重算

        def _request_relayout():
            self._resize_timer.start()

        def _apply_canvas_resize():
            rect = self.scene.sceneRect()
            # 同步 SCENE_W/H，供布局算法使用
            self.SCENE_W = rect.width()
            self.SCENE_H = rect.height()
            self.relayout_and_animate()

        self._resize_timer.timeout.connect(_apply_canvas_resize)
        self.view.resized.connect(_request_relayout)

        # 首次显示后，同步一次场景矩形并布局
        QtCore.QTimer.singleShot(0, _apply_canvas_resize)

    # ===== 信息与工具 =====
    def on_speed_changed(self, val: int):
        # 10%~400%  ->  0.1x~4.0x
        self.speed_mult = max(0.1, val / 100.0)
        approx = int(self.base_anim_ms / self.speed_mult)
        self.status.setText(f"动画速度：{self.speed_mult:.2f}x（时长≈{approx} ms）")

    def update_info_panels(self, last_action: str = ""):
        inorder = self.bst.inorder()
        self.info_state.setText(f"节点数：{len(inorder)}，深度：{self.bst.depth()}，中序：{inorder}")
        if last_action:
            self.info_last.setText(last_action)

    def on_node_selected(self, key: int):
        path, _ = self.bst.search(key)
        self.info_selected.setText(f"键：{key}，路径：{[n.key for n in path]}")

    def parse_numbers(self) -> List[int]:
        text = self.input_edit.text().replace(',', ' ').replace('，', ' ')
        nums: List[int] = []
        for t in text.split():
            try: nums.append(int(t))
            except: pass
        return nums

    def show_info(self, title: str, msg: str):
        QtWidgets.QMessageBox.information(self, title, msg)

    # ===== 交互 =====
    def on_insert_clicked(self):
        nums = self.parse_numbers() or ([int(self.input_edit.text().strip())] if self.input_edit.text().strip().isdigit() else [])
        if not nums: self.show_info("插入", "请输入至少一个整数。"); return
        dup = []
        for x in nums:
            node, parent = self.bst.insert(x)
            if node is None: dup.append(x); continue
            item = NodeItem(x); item.on_click = self.on_node_selected
            start_pos = self.node_item[parent].pos() if (parent and parent in self.node_item) else QtCore.QPointF(self.SCENE_W/2, self.margin)
            item.setPos(start_pos); self.scene.addItem(item); self.node_item[node] = item
        self.relayout_and_animate()
        if dup: self.show_info("插入", f"已存在：{dup}")
        self.status.setText(f"当前节点数：{len(self.node_item)}"); self.input_edit.clear(); self.update_info_panels("插入完成")

    def on_search_clicked(self):
        nums = self.parse_numbers() or ([int(self.input_edit.text().strip())] if self.input_edit.text().strip().isdigit() else [])
        if not nums: self.show_info("查找", "请输入要查找的整数。"); return
        key = nums[0]
        path, node = self.bst.search(key)
        if not path: self.show_info("查找", "树为空。"); self.input_edit.clear(); return
        self.flash_path(path, found=(node is not None))
        self.show_info("查找", f"{'找到' if node else '未找到'} {key}")
        self.input_edit.clear(); self.update_info_panels("查找完成")

    def on_delete_clicked(self):
        nums = self.parse_numbers() or ([int(self.input_edit.text().strip())] if self.input_edit.text().strip().isdigit() else [])
        if not nums: self.show_info("删除", "请输入要删除的整数。"); return
        key = nums[0]
        removed_node = self.bst.delete(key)
        if removed_node is None: self.show_info("删除", f"未找到 {key}"); return
        item = self.node_item.pop(removed_node, None)
        if item is not None: self.remove_item_immediately(item)
        self.cleanup_orphans(); self.relayout_and_animate()
        self.show_info("删除", f"已删除 {key}")
        self.status.setText(f"当前节点数：{len(self.node_item)}"); self.input_edit.clear(); self.update_info_panels("删除完成")

    def on_clear_clicked(self):
        self.bst.clear()
        for it in list(self.node_item.values()): self.remove_item_immediately(it)
        self.node_item.clear(); self.clear_edges(); self.view.viewport().update()
        self.status.setText("已清空"); self.input_edit.clear(); self.update_info_panels("已清空")

    def on_random_clicked(self):
        n = self.spin_random.value()
        existing = set(self.bst.inorder())
        lo, hi = 0, max(100, n*20)
        cand = list(set(range(lo, hi)) - existing); random.shuffle(cand)
        nums = cand[:n]
        self.input_edit.setText(" ".join(map(str, nums)))
        self.on_insert_clicked()

    # ===== 动画/布局/连线 =====
    def relayout_and_animate(self):
        if not self.bst.root: self.clear_edges(); return
        positions, radius = self.compute_layout()
        if self.chk_anim.isChecked(): self.animate_to_positions(positions, radius)
        else:
            for n, item in list(self.node_item.items()):
                if n in positions: item.set_radius(radius); item.setPos(positions[n])
            self.clear_edges()
        self.rebuild_edges(positions, radius)

    def compute_layout(self) -> Tuple[Dict[BSTNode, QtCore.QPointF], float]:
        index = 0; x_index: Dict[BSTNode, int] = {}; depth: Dict[BSTNode, int] = {}
        def dfs(n: Optional[BSTNode], d: int):
            nonlocal index
            if not n: return
            depth[n] = d; dfs(n.left, d+1); x_index[n] = index; index += 1; dfs(n.right, d+1)
        dfs(self.bst.root, 0)
        if not x_index: return {}, 20.0
        n_nodes = len(x_index); max_depth = max(depth.values()) if depth else 0
        base_radius = 24.0; min_radius = 12.0; max_radius = 28.0
        base_h_gap = 3.2 * base_radius; base_v_gap = 4.0 * base_radius
        width_units = max(1, n_nodes-1)*base_h_gap + 2*base_radius
        height_units = max(1, max_depth)*base_v_gap + 2*base_radius
        avail_w = self.SCENE_W - 2*self.margin
        avail_h = self.SCENE_H - 2*self.margin
        s = min(avail_w/width_units, avail_h/height_units, 1.2)
        radius = max(min_radius, min(max_radius, base_radius*s))
        h_gap = base_h_gap*s; v_gap = base_v_gap*s
        positions: Dict[BSTNode, QtCore.QPointF] = {}
        total_w = (n_nodes-1)*h_gap + 2*radius; total_h = max(0, max_depth)*v_gap + 2*radius
        offset_x = (self.SCENE_W - total_w)/2 + radius; offset_y = (self.SCENE_H - total_h)/2 + radius
        for n, xi in x_index.items():
            positions[n] = QtCore.QPointF(offset_x + xi*h_gap, offset_y + depth[n]*v_gap)
        return positions, radius

    def animate_to_positions(self, positions: Dict[BSTNode, QtCore.QPointF], radius: float):
        for a in self.animations: a.stop()
        self.animations.clear()
        for n, item in list(self.node_item.items()):
            if n not in positions:
                if item.scene() is not None: self.scene.removeItem(item)
                self.node_item.pop(n, None); continue
            item.set_radius(radius)
            start = item.pos(); end = positions[n]
            if (start - end).manhattanLength() < 0.5:
                item.setPos(end); continue
            anim = QtCore.QVariantAnimation(self)
            # 核心：速度越大 -> 持续越短
            duration = max(30, int(self.base_anim_ms / self.speed_mult))
            anim.setDuration(duration)
            anim.setStartValue(start); anim.setEndValue(end)
            anim.valueChanged.connect(lambda v, it=item: it.setPos(v))
            anim.start(); self.animations.append(anim)

    def remove_item_immediately(self, item: NodeItem):
        try:
            item.setVisible(False)
            for ch in list(item.childItems()):
                if ch.scene() is not None: self.scene.removeItem(ch)
            if item.scene() is not None: self.scene.removeItem(item)
        finally:
            self.view.viewport().update()

    def clear_edges(self):
        for e in self.edge_items: self.scene.removeItem(e)
        self.edge_items.clear()

    def rebuild_edges(self, positions: Dict[BSTNode, QtCore.QPointF], radius: float):
        self.clear_edges()
        relations: List[Tuple[EdgeItem, BSTNode, BSTNode]] = []
        for n, pos in positions.items():
            if n.left is not None and n.left in positions:
                e = EdgeItem(pos, positions[n.left], radius); self.scene.addItem(e); self.edge_items.append(e); relations.append((e, n, n.left))
            if n.right is not None and n.right in positions:
                e = EdgeItem(pos, positions[n.right], radius); self.scene.addItem(e); self.edge_items.append(e); relations.append((e, n, n.right))
        def refresh_edges():
            for e, pnode, cnode in relations:
                if pnode in self.node_item and cnode in self.node_item:
                    e.r = self.node_item[pnode].radius
                    e.update_path(self.node_item[pnode].pos(), self.node_item[cnode].pos())
        if self.animations:
            timer = QtCore.QTimer(self); timer.setInterval(16); timer.timeout.connect(refresh_edges)
            def stop_timer():
                if not any(a.state() == QtCore.QAbstractAnimation.Running for a in self.animations):
                    timer.stop(); refresh_edges()
            timer.timeout.connect(stop_timer); timer.start()
        else:
            refresh_edges()

    def flash_path(self, path: List[BSTNode], found: bool):
        # 基准（原先的固定值）
        base_highlight = 180
        base_gap = 40
        base_final = 300

        # 速度缩放：更快 -> 时间更短
        k = max(0.1, self.speed_mult)
        highlight_ms = max(40, int(base_highlight / k))
        gap_ms = max(16, int(base_gap / k))
        final_ms = max(60, int(base_final / k))

        total_ms = 0
        for n in path:
            item = self.node_item.get(n)
            if not item: continue
            QtCore.QTimer.singleShot(total_ms, lambda it=item: it.highlight(True))
            QtCore.QTimer.singleShot(total_ms + highlight_ms, lambda it=item: it.highlight(False))
            total_ms += highlight_ms + gap_ms

        if path:
            last_item = self.node_item.get(path[-1])
            if last_item:
                ms = total_ms + gap_ms
                QtCore.QTimer.singleShot(ms, lambda it=last_item: it.highlight(True))
                QtCore.QTimer.singleShot(ms + final_ms, lambda it=last_item: it.highlight(False))

    def cleanup_orphans(self):
        alive: Set[BSTNode] = set(self.bst.nodes())
        for n, item in list(self.node_item.items()):
            if n not in alive:
                self.remove_item_immediately(item)
                self.node_item.pop(n, None)
        self.view.viewport().update()

# =============================
# 启动
# =============================

def main():
    # HiDPI 支持（必须在 QApplication 之前设置）
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

    app = QtWidgets.QApplication(sys.argv)

    # Windows 全局字体（照顾到未走 _get_ui_font 的控件）
    if IS_WIN:
        app.setFont(QtGui.QFont(_pick_win_yahei_family(), 10))

    win = BSTVisualizer()
    win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

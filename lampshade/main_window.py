import os
from random import randint, uniform

import numpy as np
from PyQt6 import QtCore, QtWidgets

from .params import Params
from .geometry import build_mesh_arrays, build_trimesh_for_export
from .viewer import MeshViewer


class MainWindow(QtWidgets.QMainWindow):
    """
    Main GUI window:
      - Parameter controls (sliders and combos)
      - Real-time 3D preview
      - Export/save/load/randomize actions
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lampshade Generator")
        self.P = Params()

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        h = QtWidgets.QHBoxLayout(central)

        # Controls on the left
        self.controls = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(self.controls)
        form.setFieldGrowthPolicy(QtWidgets.QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        h.addWidget(self.controls, 0)

        # 3D viewer on the right
        self.viewer = MeshViewer()
        h.addWidget(self.viewer, 1)

        # Sliders (primary parameters)
        self.s_top, _ = self._new_slider(form, "Top Diameter", self.P.topDiameterMin, self.P.topDiameterMax, self.P.topDiameter, step=1)
        self.s_mid, _ = self._new_slider(form, "Middle Diameter", self.P.middleDiameterMin, self.P.middleDiameterMax, self.P.middleDiameter, step=1)
        self.s_bot, _ = self._new_slider(form, "Bottom Diameter", self.P.bottomDiameterMin, self.P.bottomDiameterMax, self.P.bottomDiameter, step=1)
        self.s_h,   _ = self._new_slider(form, "Cylinder Height", self.P.cylinderHeightMin, self.P.cylinderHeightMax, self.P.cylinderHeight, step=1)

        self.s_fc, _ = self._new_slider(form, "Feature Count", self.P.featureCountMin, self.P.featureCountMax, self.P.featureCount, step=1)
        self.s_fd, self.fd_lbl, self.fd_scale, self.fd_decimals = self._new_fslider(form, "Feature Depth", self.P.featureDepthMin, self.P.featureDepthMax, self.P.featureDepth, step=0.01, decimals=2)

        # Design mode and interpolation
        self.combo_mode = QtWidgets.QComboBox()
        modes = [
            ("Ripples", 1), ("Spirals", 2), ("Ridges", 3), ("Crosshatch", 4), ("Double sine", 5),
            ("Twisted pulse", 6), ("Weave", 7), ("Moire", 8),
            ("Michelin", 9), ("Michelin (spitz)", 10), ("Michelin (Spirale)", 11),
            ("Shards", 12), ("None", 0)
        ]
        for name, val in modes:
            self.combo_mode.addItem(name, userData=val)
        self.combo_mode.setCurrentIndex(0)
        form.addRow("Design Mode", self.combo_mode)

        self.combo_interp = QtWidgets.QComboBox()
        self.combo_interp.addItems(["Bezier", "Lagrange", "Linear"])
        self.combo_interp.setCurrentIndex(0)
        form.addRow("Interpolation", self.combo_interp)

        # Resolution and angle at the bottom
        self.s_det, _ = self._new_slider(form, "Detail (resolution)", self.P.detailMin, self.P.detailMax, self.P.detail, step=1)
        self.s_ang, _ = self._new_slider(form, "Overhang Angle", self.P.overhangAngleMin, self.P.overhangAngleMax, self.P.overhangAngle, step=1)

        # Actions
        btn_row = QtWidgets.QHBoxLayout()
        self.btn_random = QtWidgets.QPushButton("Randomize")
        self.btn_export = QtWidgets.QPushButton("Export STL")
        self.btn_save   = QtWidgets.QPushButton("Save Design")
        self.btn_load   = QtWidgets.QPushButton("Load Design")
        btn_row.addWidget(self.btn_random)
        btn_row.addWidget(self.btn_export)
        btn_row.addWidget(self.btn_save)
        btn_row.addWidget(self.btn_load)
        form.addRow(btn_row)

        # Output log
        self.log = QtWidgets.QPlainTextEdit()
        self.log.setReadOnly(True)
        form.addRow("Output", self.log)

        # Debounced updates to prevent rebuilding on every tick while dragging sliders
        self.update_timer = QtCore.QTimer(self)
        self.update_timer.setSingleShot(True)
        self.update_timer.setInterval(250)
        self.update_timer.timeout.connect(self.rebuild_mesh_now)

        # Connect signals
        for w in [self.s_top, self.s_mid, self.s_bot, self.s_h, self.s_fc, self.s_fd, self.s_det, self.s_ang]:
            w.valueChanged.connect(self.schedule_rebuild)
        self.combo_mode.currentIndexChanged.connect(self.schedule_rebuild)
        self.combo_interp.currentIndexChanged.connect(self.schedule_rebuild)

        self.btn_random.clicked.connect(self.on_randomize)
        self.btn_export.clicked.connect(self.on_export)
        self.btn_save.clicked.connect(self.on_save)
        self.btn_load.clicked.connect(self.on_load)

        # Initial build
        self.rebuild_mesh_now()

    # ----- UI helpers -----
    def _new_slider(self, form, label, mn, mx, val, step=1):
        s = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        s.setRange(mn, mx)
        s.setSingleStep(step)
        s.setPageStep(step)
        s.setValue(val)
        lbl = QtWidgets.QLabel(str(val))
        s.valueChanged.connect(lambda v: lbl.setText(str(v)))
        container = QtWidgets.QWidget()
        hl = QtWidgets.QHBoxLayout(container)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.addWidget(s)
        hl.addWidget(lbl)
        form.addRow(label, container)
        return s, lbl

    def _new_fslider(self, form, label, mn, mx, val, step=0.01, decimals=2):
        scale = 10 ** decimals
        s = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        s.setRange(int(mn * scale), int(mx * scale))
        s.setSingleStep(int(step * scale))
        s.setPageStep(int(step * scale))
        s.setValue(int(val * scale))
        lbl = QtWidgets.QLabel(f"{val:.{decimals}f}")
        def upd(v):
            lbl.setText(f"{v/scale:.{decimals}f}")
        s.valueChanged.connect(upd)
        container = QtWidgets.QWidget()
        hl = QtWidgets.QHBoxLayout(container)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.addWidget(s)
        hl.addWidget(lbl)
        form.addRow(label, container)
        return s, lbl, scale, decimals

    # ----- Sync & rebuild -----
    def schedule_rebuild(self):
        self.sync_params_from_ui()
        self.update_timer.start()

    def sync_params_from_ui(self):
        P = self.P
        P.topDiameter = int(self.s_top.value())
        P.middleDiameter = int(self.s_mid.value())
        P.bottomDiameter = int(self.s_bot.value())
        P.cylinderHeight = int(self.s_h.value())
        P.detail = int(self.s_det.value())
        P.overhangAngle = int(self.s_ang.value())
        P.featureCount = int(self.s_fc.value())
        P.featureDepth = float(self.s_fd.value()) / float(self.fd_scale)
        P.designMode = int(self.combo_mode.currentData())
        P.interpolation = {0: 0, 1: 1, 2: 2}[self.combo_interp.currentIndex()]

        P.update_transition()
        P.update_feature_depth_max()

        # Keep feature depth slider in a valid range as geometry changes
        new_max = int(max(P.featureDepthMin, P.featureDepthMax) * self.fd_scale)
        if self.s_fd.maximum() != new_max:
            self.s_fd.setMaximum(new_max)
        if self.s_fd.value() > new_max:
            self.s_fd.setValue(new_max)

    def rebuild_mesh_now(self):
        P = self.P
        V, F = build_mesh_arrays(P)
        if V.size > 0:
            bbmin = V.min(axis=0)
            bbmax = V.max(axis=0)
            diag = float(np.linalg.norm(bbmax - bbmin))
            self.viewer.view.camera.distance = max(100.0, diag * 1.2)
            self.viewer.view.camera.center = tuple(((bbmin + bbmax) * 0.5))
        self.viewer.set_mesh(V, F)

    def log_line(self, s: str):
        self.log.appendPlainText(s)
        self.log.ensureCursorVisible()

    # ----- Actions -----
    def on_randomize(self):
        P = self.P

        # Keep resolution and overhang as-is; randomize the rest
        P.topDiameter = randint(P.topDiameterMin, P.topDiameterMax)
        P.middleDiameter = randint(P.middleDiameterMin, P.middleDiameterMax)
        P.bottomDiameter = randint(P.bottomDiameterMin, P.bottomDiameterMax)
        P.cylinderHeight = randint(P.cylinderHeightMin, P.cylinderHeightMax)
        P.featureCount = randint(P.featureCountMin, P.featureCountMax)
        P.designMode = randint(0, 12)  # includes "None"
        P.interpolation = randint(0, 2)  # Bezier/Lagrange/Linear

        P.update_transition()
        P.update_feature_depth_max()
        P.featureDepth = uniform(P.featureDepthMin, max(P.featureDepthMin, P.featureDepthMax))

        # Push to UI (signals blocked to avoid intermediate rebuilds)
        blockers = [
            QtCore.QSignalBlocker(self.s_top),
            QtCore.QSignalBlocker(self.s_mid),
            QtCore.QSignalBlocker(self.s_bot),
            QtCore.QSignalBlocker(self.s_h),
            QtCore.QSignalBlocker(self.s_fc),
            QtCore.QSignalBlocker(self.s_fd),
            QtCore.QSignalBlocker(self.combo_mode),
            QtCore.QSignalBlocker(self.combo_interp),
        ]
        try:
            self.s_top.setValue(P.topDiameter)
            self.s_mid.setValue(P.middleDiameter)
            self.s_bot.setValue(P.bottomDiameter)
            self.s_h.setValue(P.cylinderHeight)
            self.s_fc.setValue(P.featureCount)
            self.s_fd.setMaximum(int(max(P.featureDepthMin, P.featureDepthMax) * self.fd_scale))
            self.s_fd.setValue(int(P.featureDepth * self.fd_scale))
            idx_mode = self.combo_mode.findData(P.designMode)
            if idx_mode >= 0:
                self.combo_mode.setCurrentIndex(idx_mode)
            self.combo_interp.setCurrentIndex(P.interpolation)
        finally:
            del blockers

        self.sync_params_from_ui()
        self.rebuild_mesh_now()

    def on_export(self):
        self.sync_params_from_ui()
        suggested = self.P.name() + ".stl"
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save STL As", suggested, "STL files (*.stl)")
        if not path:
            return
        try:
            self.log_line("Building mesh for export...")
            mesh = build_trimesh_for_export(self.P)
            mesh.export(path)
            self.log_line(f"Export complete: {path}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Export failed", str(e))

    def on_save(self):
        self.sync_params_from_ui()
        suggested = self.P.name() + ".txt"
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save Design As", suggested, "Text files (*.txt)")
        if not path:
            return
        try:
            line = ",".join(map(str, [
                self.P.topDiameter, self.P.middleDiameter, self.P.bottomDiameter,
                self.P.cylinderHeight, self.P.featureCount,
                self.P.featureDepth, self.P.detail, self.P.overhangAngle, self.P.designMode
            ]))
            with open(path, "w") as f:
                f.write(line + "\n")
            self.log_line(f"Design saved: {path}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Save failed", str(e))

    def on_load(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Load Design", "", "Text files (*.txt)")
        if not path:
            return
        try:
            with open(path, "r") as f:
                line = f.read().strip()
            toks = line.split(",")
            if len(toks) < 9:
                raise ValueError("Invalid design file format.")
            P = self.P
            P.topDiameter    = int(toks[0])
            P.middleDiameter = int(toks[1])
            P.bottomDiameter = int(toks[2])
            P.cylinderHeight = int(toks[3])
            P.featureCount   = int(toks[4])
            P.featureDepth   = float(toks[5])
            P.detail         = int(toks[6])
            P.overhangAngle  = int(toks[7])
            P.designMode     = int(toks[8])
            P.update_transition()
            P.update_feature_depth_max()

            # Push to UI
            self.s_top.setValue(P.topDiameter)
            self.s_mid.setValue(P.middleDiameter)
            self.s_bot.setValue(P.bottomDiameter)
            self.s_h.setValue(P.cylinderHeight)
            self.s_det.setValue(P.detail)
            self.s_ang.setValue(P.overhangAngle)
            self.s_fc.setValue(P.featureCount)
            self.s_fd.setMaximum(int(max(P.featureDepthMin, P.featureDepthMax) * self.fd_scale))
            self.s_fd.setValue(int(P.featureDepth * self.fd_scale))
            idx = self.combo_mode.findData(P.designMode)
            if idx >= 0:
                self.combo_mode.setCurrentIndex(idx)

            self.log_line(f"Design loaded: {path}")
            self.rebuild_mesh_now()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Load failed", str(e))
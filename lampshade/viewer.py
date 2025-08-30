import math
import numpy as np

from PyQt6 import QtWidgets
from vispy import scene, app as vispy_app

# Ensure vispy uses PyQt6 backend once per process
vispy_app.use_app('pyqt6')


class MeshViewer(QtWidgets.QWidget):
    """
    Qt widget embedding a vispy canvas for real-time preview.

    Lighting is camera-relative: the light direction is updated every draw
    call so the illuminated side always faces the camera.

    Still looks a bit buggy but good enough.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Vispy canvas and camera
        self.canvas = scene.SceneCanvas(keys='interactive', bgcolor='white', size=(900, 900), show=True)
        self.view = self.canvas.central_widget.add_view()
        self.view.camera = scene.cameras.TurntableCamera(
            fov=45, azimuth=35.0, elevation=35.0, distance=250.0, up='+y', center=(0, 0, 0)
        )
        scene.visuals.XYZAxis(parent=self.view.scene)

        # Mesh visual
        self.mesh_visual = scene.visuals.Mesh(shading='smooth', parent=self.view.scene, color=(1.0, 1.0, 1.0, 1.0))
        layout.addWidget(self.canvas.native)

        # Keep light aligned to camera
        self.canvas.events.draw.connect(self._on_draw)
        self._configure_lighting_defaults()
        self.update_light()

    def _configure_lighting_defaults(self) -> None:
        """
        Tweak ambient/specular if supported by the shading filter.
        Different vispy versions expose different attributes.
        """
        flt = getattr(self.mesh_visual, 'shading_filter', None)
        if flt is not None:
            try:
                if hasattr(flt, 'ambient_light'):
                    flt.ambient_light = 0.25
                if hasattr(flt, 'specular_light'):
                    flt.specular_light = 0.2
            except Exception:
                pass

    def _on_draw(self, event) -> None:
        self.update_light()

    def _camera_position(self) -> np.ndarray:
        """
        Reconstruct camera world position from turntable params.
        Turntable camera uses spherical coords around 'center'.
        """
        cam = self.view.camera
        cx, cy, cz = cam.center
        r = cam.distance
        elev = math.radians(cam.elevation)
        azim = math.radians(cam.azimuth)
        x = cx + r * math.cos(elev) * math.cos(azim)
        y = cy + r * math.sin(elev)
        z = cz + r * math.cos(elev) * math.sin(azim)
        return np.array([x, y, z], dtype=float)

    def update_light(self) -> None:
        """
        Point the directional light from camera toward the scene center.
        This stabilizes shading as the user rotates the view.
        """
        cam_pos = self._camera_position()
        center = np.array(self.view.camera.center, dtype=float)
        dir_vec = center - cam_pos
        n = np.linalg.norm(dir_vec)
        if n < 1e-9:
            return
        dir_vec = (dir_vec / n).astype(float)

        flt = getattr(self.mesh_visual, 'shading_filter', None)
        try:
            if flt is not None and hasattr(flt, 'light_dir'):
                flt.light_dir = tuple(dir_vec.tolist())
                self.mesh_visual.update()
            elif flt is not None and hasattr(flt, 'lights') and flt.lights:
                light = flt.lights[0]
                if hasattr(light, 'direction'):
                    light.direction = tuple(dir_vec.tolist())
                    self.mesh_visual.update()
        except Exception:
            pass

    def set_mesh(self, V: np.ndarray, F: np.ndarray) -> None:
        if V.size == 0 or F.size == 0:
            self.mesh_visual.set_data(vertices=np.zeros((0, 3)), faces=np.zeros((0, 3), dtype=np.int32))
            return
        self.mesh_visual.set_data(vertices=V.astype(np.float32), faces=F.astype(np.int32))
        self.update_light()
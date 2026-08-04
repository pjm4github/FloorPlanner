from PyQt6.QtWidgets import QApplication
import pyqtgraph.opengl as gl
from OpenGL import GL
app = QApplication([])
v = gl.GLViewWidget()
v.show()
app.processEvents()
v.makeCurrent()
for n in ("VENDOR", "RENDERER", "VERSION", "SHADING_LANGUAGE_VERSION"):
    print(f"{n:26} {GL.glGetString(getattr(GL, 'GL_' + n)).decode()}")

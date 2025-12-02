"""Process executor for running KooMeshModifier"""
import os
import sys
from pathlib import Path
from PySide6.QtCore import QObject, Signal, QProcess

class ProcessExecutor(QObject):
    """Executes KooMeshModifier and captures output"""
    output = Signal(str)
    error = Signal(str)
    finished = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.process: QProcess = None
        self._running = False

    def run(self, script_path: str, koomesh_path: str = None):
        """Run KooMeshModifier with the given script"""
        if self._running:
            self.error.emit("이미 프로세스가 실행 중입니다.")
            return

        # Determine KooMeshModifier path
        if not koomesh_path:
            # Default: look in project directory
            project_dir = Path(__file__).parent.parent
            if sys.platform == 'win32':
                koomesh_path = str(project_dir / "KooMeshModifier" / "run.bat")
            else:
                koomesh_path = str(project_dir / "KooMeshModifier" / "run.sh")

        # Check if executable exists
        if not Path(koomesh_path).exists():
            self.error.emit(f"KooMeshModifier를 찾을 수 없습니다: {koomesh_path}")
            self.finished.emit(1)
            return

        # Setup process
        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self._on_stdout)
        self.process.readyReadStandardError.connect(self._on_stderr)
        self.process.finished.connect(self._on_finished)

        # Set working directory to script location
        script_dir = str(Path(script_path).parent)
        self.process.setWorkingDirectory(script_dir)

        # Run
        self._running = True
        script_name = Path(script_path).name

        if sys.platform == 'win32':
            self.process.start(koomesh_path, [script_name])
        else:
            # Make sure script is executable
            os.chmod(koomesh_path, 0o755)
            self.process.start("/bin/bash", [koomesh_path, script_name])

    def _on_stdout(self):
        data = self.process.readAllStandardOutput().data().decode('utf-8', errors='replace')
        self.output.emit(data)

    def _on_stderr(self):
        data = self.process.readAllStandardError().data().decode('utf-8', errors='replace')
        self.error.emit(data)

    def _on_finished(self, exit_code: int):
        self._running = False
        self.finished.emit(exit_code)

    def stop(self):
        """Stop the running process"""
        if self.process and self._running:
            self.process.kill()
            self._running = False

    @property
    def is_running(self) -> bool:
        return self._running

"""Remove Duplicate Tied Contacts method"""
from PySide6.QtWidgets import QVBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt
from .base import BaseContactMethod


class RemoveDuplicateTiedMethod(BaseContactMethod):
    """중복 Tied Contact 제거 메소드"""

    @property
    def method_id(self) -> str:
        return "remove_duplicate_tied"

    @property
    def method_name(self) -> str:
        return "중복 Tied Contact 제거"

    def _setup_ui(self):
        """이 메소드는 별도 옵션 없음"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # 설명 프레임
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                background-color: #1e3a5f;
                border: 1px solid #3b82f6;
                border-radius: 8px;
                padding: 16px;
            }
        """)
        info_layout = QVBoxLayout(info_frame)

        title = QLabel("중복된 Tied Contact 제거")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #60a5fa;")
        info_layout.addWidget(title)

        desc = QLabel(
            "K파일 내에서 중복 정의된 Tied Contact를 자동으로 탐지하고 제거합니다.\n"
            "동일한 Master/Slave Part 조합을 가진 Contact 중 첫 번째만 유지합니다."
        )
        desc.setStyleSheet("font-size: 12px; color: #d1d5db;")
        desc.setWordWrap(True)
        info_layout.addWidget(desc)

        layout.addWidget(info_frame)

        # 옵션 없음 안내
        no_option = QLabel("이 메소드는 별도의 옵션이 필요하지 않습니다.")
        no_option.setStyleSheet("font-size: 12px; color: #9ca3af; font-style: italic;")
        no_option.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(no_option)

        layout.addStretch()

    def generate_script(self, k_filename: str) -> str:
        """스크립트 생성"""
        lines = [
            "*Inputfile",
            k_filename,
            "*Mode",
            "REMOVE_DUPLICATE_TIED_CONTACTS,1",
            "**RemoveDuplicateTiedContacts",
            "remove_duplicate_tied_contacts,True",
            "**EndRemoveDuplicateTiedContacts",
            "*End"
        ]
        return "\n".join(lines)

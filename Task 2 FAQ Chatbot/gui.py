"""
Modern ChatGPT-styled Desktop Interface for FAQ Chatbot.
Built with PySide6 (Qt for Python).
"""

import os
import sys

# Import chatbot logic and pandas first to avoid Shiboken meta-path importer conflicts
from chatbot import initialize_chatbot, get_response, DEFAULT_SIMILARITY_THRESHOLD, FALLBACK_RESPONSE

from PySide6.QtCore import Qt, QSize, Signal, QTimer
from PySide6.QtGui import QFont, QColor, QIcon, QPainter, QPainterPath, QCursor
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QScrollArea, QLineEdit, QTextEdit, QPushButton, QLabel, QFrame,
    QSplitter, QListWidget, QListWidgetItem, QGraphicsDropShadowEffect,
    QSizePolicy
)

# ================= THEME STYLESHEETS (ChatGPT Sleek Dark) =================
STYLESHEET = """
QMainWindow {
    background-color: #212121;
}

QWidget {
    color: #ececf1;
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, 'Roboto', sans-serif;
    font-size: 14px;
}

/* Sidebar Styling */
#sidebar {
    background-color: #171717;
    border-right: 1px solid #282828;
}

#sidebarHeader {
    background-color: transparent;
    padding: 10px;
}

#newChatBtn {
    background-color: #212121;
    color: #ececf1;
    border: 1px solid #333333;
    border-radius: 8px;
    padding: 10px 14px;
    text-align: left;
    font-weight: 600;
    font-size: 13px;
}
#newChatBtn:hover {
    background-color: #2a2a2a;
    border-color: #4a4a4a;
}
#newChatBtn:pressed {
    background-color: #1f1f1f;
}

#toggleSidebarBtn, #iconBtn {
    background-color: transparent;
    color: #b4b4b4;
    border: none;
    border-radius: 6px;
    padding: 6px;
}
#toggleSidebarBtn:hover, #iconBtn:hover {
    background-color: #2a2a2a;
    color: #ffffff;
}

#historyList {
    background-color: transparent;
    border: none;
    outline: none;
    padding: 4px;
}
#historyList::item {
    color: #b4b4b4;
    background-color: transparent;
    border-radius: 8px;
    padding: 10px 12px;
    margin: 2px 0px;
    font-size: 13px;
}
#historyList::item:hover {
    background-color: #212121;
    color: #ececf1;
}
#historyList::item:selected {
    background-color: #2a2b32;
    color: #ffffff;
    font-weight: 500;
}

#sidebarFooter {
    border-top: 1px solid #262626;
    padding: 12px 14px;
    background-color: transparent;
}

/* Main Content Area */
#mainContent {
    background-color: #212121;
}

#topBar {
    background-color: #212121;
    border-bottom: 1px solid #2b2b2b;
    padding: 8px 16px;
}

#modelTitle {
    color: #ececf1;
    font-size: 15px;
    font-weight: 600;
}

#statusPill {
    background-color: #1a332a;
    color: #10a37f;
    border-radius: 10px;
    padding: 2px 8px;
    font-size: 11px;
    font-weight: 600;
}

/* Chat Messages */
QScrollArea {
    background-color: transparent;
    border: none;
}
#chatScrollWidget {
    background-color: #212121;
}

/* Scrollbars */
QScrollBar:vertical {
    background: transparent;
    width: 8px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #383838;
    min-height: 24px;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background: #4a4a4a;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
    height: 0px;
}

/* Suggestions on Landing Page */
#landingTitle {
    color: #ffffff;
    font-size: 28px;
    font-weight: 600;
    margin-bottom: 24px;
}

#suggestionCard {
    background-color: #212121;
    color: #d1d5db;
    border: 1px solid #333333;
    border-radius: 14px;
    padding: 14px 18px;
    text-align: left;
    font-size: 13px;
}
#suggestionCard:hover {
    background-color: #2a2b32;
    border-color: #4b4d58;
    color: #ffffff;
}

/* Floating Input Container */
#inputWrapper {
    background-color: transparent;
    padding: 0px 30px 14px 30px;
}

#inputCard {
    background-color: #2f2f2f;
    border: 1px solid #3e3e3e;
    border-radius: 24px;
    padding: 8px 12px;
}

#inputCard:focus-within {
    border: 1px solid #565869;
}

#chatInput {
    background-color: transparent;
    color: #ffffff;
    border: none;
    font-size: 14px;
    padding: 4px 8px;
}

#sendButton {
    background-color: #676767;
    color: #171717;
    border: none;
    border-radius: 17px;
    width: 34px;
    height: 34px;
    font-size: 16px;
    font-weight: bold;
}
#sendButton[active="true"] {
    background-color: #ffffff;
    color: #000000;
}
#sendButton[active="true"]:hover {
    background-color: #e3e3e3;
}

#disclaimerLbl {
    color: #7d7d8e;
    font-size: 11px;
    margin-top: 6px;
}
"""


class AutoResizingTextEdit(QTextEdit):
    """Multi-line text input that sends on Enter and adds newline on Shift+Enter."""
    sendRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("chatInput")
        self.setPlaceholderText("Ask anything about admissions, eligibility, fees, scholarships...")
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setMaximumHeight(120)
        self.setMinimumHeight(38)
        self.textChanged.connect(self.adjust_height)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if event.modifiers() & Qt.ShiftModifier:
                super().keyPressEvent(event)
            else:
                event.accept()
                self.sendRequested.emit()
        else:
            super().keyPressEvent(event)

    def adjust_height(self):
        doc_height = int(self.document().size().height())
        new_height = max(38, min(120, doc_height + 10))
        self.setFixedHeight(new_height)


class MessageBubble(QWidget):
    """Renders a formatted user or assistant message block with ChatGPT-like styling."""
    def __init__(self, sender_type: str, text: str, score: float = None, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(6)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        if sender_type == "user":
            avatar = QLabel("👤")
            avatar.setStyleSheet("font-size: 14px;")
            name = QLabel("You")
            name.setStyleSheet("font-weight: bold; color: #ececf1; font-size: 13px;")
            header_layout.addWidget(avatar)
            header_layout.addWidget(name)
            header_layout.addStretch()

            # User Bubble
            bubble = QFrame()
            bubble.setStyleSheet("""
                background-color: #2f2f2f;
                border-radius: 14px;
                padding: 12px 16px;
                border: 1px solid #383838;
            """)
            b_layout = QVBoxLayout(bubble)
            b_layout.setContentsMargins(14, 10, 14, 10)
            
            lbl = QLabel(text)
            lbl.setWordWrap(True)
            lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
            lbl.setStyleSheet("color: #ffffff; font-size: 14px; line-height: 1.4;")
            b_layout.addWidget(lbl)

            layout.addLayout(header_layout)
            layout.addWidget(bubble)

        else:
            # Assistant Response
            avatar = QLabel("✨")
            avatar.setStyleSheet("font-size: 14px; color: #10a37f;")
            name = QLabel("FAQ Assistant")
            name.setStyleSheet("font-weight: bold; color: #10a37f; font-size: 13px;")
            header_layout.addWidget(avatar)
            header_layout.addWidget(name)
            header_layout.addStretch()

            # Response Text container
            content_frame = QFrame()
            content_frame.setStyleSheet("""
                background-color: transparent;
                padding: 4px 2px;
            """)
            c_layout = QVBoxLayout(content_frame)
            c_layout.setContentsMargins(24, 4, 10, 4)

            lbl = QLabel(text)
            lbl.setWordWrap(True)
            lbl.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.LinksAccessibleByMouse)
            lbl.setOpenExternalLinks(True)
            lbl.setStyleSheet("color: #d1d5db; font-size: 14px; line-height: 1.5;")
            c_layout.addWidget(lbl)

            layout.addLayout(header_layout)
            layout.addWidget(content_frame)


class ModernChatGPTGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FAQ Assistant")
        self.resize(1080, 740)
        self.setMinimumSize(700, 500)
        self.setStyleSheet(STYLESHEET)

        # Chat history memory & active conversation
        self.chat_history = []  # list of tuples: (query, answer, score)
        self.current_conversation = []

        # Initialize Chatbot Engine
        self.init_chatbot_engine()

        # Build Main UI
        self.init_ui()

    def init_chatbot_engine(self):
        """Initializes the TF-IDF matching engine."""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        data_path = os.path.join(base_dir, "data", "faqs.csv")
        if not os.path.exists(data_path):
            data_path = os.path.join(base_dir, "GIKI_FAQ_Dataset.csv")

        try:
            self.vectorizers, self.matrices, self.faq_df = initialize_chatbot(data_path)
            self.engine_ready = True
            self.faq_count = len(self.faq_df)
        except Exception as e:
            self.engine_ready = False
            self.faq_count = 0
            self.init_error = str(e)

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ---------------- 1. LEFT SIDEBAR ----------------
        self.sidebar = QWidget()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(260)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(12, 14, 12, 12)
        sidebar_layout.setSpacing(10)

        # Sidebar Header: New Chat & Toggle Icon
        sb_header = QHBoxLayout()
        self.new_chat_btn = QPushButton("+  New chat")
        self.new_chat_btn.setObjectName("newChatBtn")
        self.new_chat_btn.setCursor(Qt.PointingHandCursor)
        self.new_chat_btn.clicked.connect(self.start_new_chat)
        sb_header.addWidget(self.new_chat_btn, stretch=1)

        self.toggle_btn_sidebar = QPushButton("◨")
        self.toggle_btn_sidebar.setObjectName("toggleSidebarBtn")
        self.toggle_btn_sidebar.setCursor(Qt.PointingHandCursor)
        self.toggle_btn_sidebar.setToolTip("Close sidebar")
        self.toggle_btn_sidebar.clicked.connect(self.toggle_sidebar)
        sb_header.addWidget(self.toggle_btn_sidebar)

        sidebar_layout.addLayout(sb_header)

        # Section Label: Recent Questions
        history_title = QLabel("Recent Questions")
        history_title.setStyleSheet("color: #71717a; font-size: 11px; font-weight: 600; padding: 12px 6px 4px 6px; text-transform: uppercase;")
        sidebar_layout.addWidget(history_title)

        # History List
        self.history_list = QListWidget()
        self.history_list.setObjectName("historyList")
        self.history_list.setCursor(Qt.PointingHandCursor)
        self.history_list.itemClicked.connect(self.on_history_item_clicked)
        sidebar_layout.addWidget(self.history_list, stretch=1)

        # Sidebar Footer: User / Status Profile
        sb_footer = QFrame()
        sb_footer.setObjectName("sidebarFooter")
        footer_layout = QHBoxLayout(sb_footer)
        footer_layout.setContentsMargins(0, 6, 0, 0)
        
        avatar_lbl = QLabel("🎓")
        avatar_lbl.setStyleSheet("background-color: #27272a; border-radius: 14px; padding: 4px 6px; font-size: 14px;")
        
        user_info = QVBoxLayout()
        user_info.setSpacing(1)
        name_lbl = QLabel("FAQ Knowledge Base")
        name_lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #ececf1;")
        count_lbl = QLabel(f"{self.faq_count} verified answers")
        count_lbl.setStyleSheet("font-size: 11px; color: #71717a;")
        user_info.addWidget(name_lbl)
        user_info.addWidget(count_lbl)

        footer_layout.addWidget(avatar_lbl)
        footer_layout.addLayout(user_info)
        footer_layout.addStretch()

        sidebar_layout.addWidget(sb_footer)

        main_layout.addWidget(self.sidebar)

        # ---------------- 2. MAIN CHAT AREA ----------------
        self.main_content = QWidget()
        self.main_content.setObjectName("mainContent")
        content_layout = QVBoxLayout(self.main_content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Top Bar
        top_bar = QWidget()
        top_bar.setObjectName("topBar")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(16, 10, 16, 10)

        self.toggle_btn_top = QPushButton("☰")
        self.toggle_btn_top.setObjectName("toggleSidebarBtn")
        self.toggle_btn_top.setCursor(Qt.PointingHandCursor)
        self.toggle_btn_top.setToolTip("Toggle sidebar")
        self.toggle_btn_top.clicked.connect(self.toggle_sidebar)
        self.toggle_btn_top.hide()  # hidden initially because sidebar is open
        top_layout.addWidget(self.toggle_btn_top)

        title_lbl = QLabel("FAQ Assistant")
        title_lbl.setObjectName("modelTitle")
        top_layout.addWidget(title_lbl)

        status_lbl = QLabel("● Ready")
        status_lbl.setObjectName("statusPill")
        top_layout.addWidget(status_lbl)

        top_layout.addStretch()

        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("newChatBtn")
        clear_btn.setCursor(Qt.PointingHandCursor)
        clear_btn.setStyleSheet("padding: 5px 12px; font-size: 12px;")
        clear_btn.clicked.connect(self.start_new_chat)
        top_layout.addWidget(clear_btn)

        content_layout.addWidget(top_bar)

        # Scrollable Chat Container
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_widget = QWidget()
        self.scroll_widget.setObjectName("chatScrollWidget")
        self.chat_layout = QVBoxLayout(self.scroll_widget)
        self.chat_layout.setContentsMargins(60, 20, 60, 20)
        self.chat_layout.setSpacing(18)
        self.chat_layout.setAlignment(Qt.AlignTop)

        self.scroll_area.setWidget(self.scroll_widget)
        content_layout.addWidget(self.scroll_area, stretch=1)

        # Landing Container (Shown when conversation is empty)
        self.build_landing_page()

        # ---------------- 3. FLOATING BOTTOM INPUT BAR ----------------
        input_wrapper = QWidget()
        input_wrapper.setObjectName("inputWrapper")
        wrapper_layout = QVBoxLayout(input_wrapper)
        wrapper_layout.setContentsMargins(60, 0, 60, 10)
        wrapper_layout.setSpacing(4)

        # Input Card (Pill Container)
        input_card = QFrame()
        input_card.setObjectName("inputCard")
        card_layout = QHBoxLayout(input_card)
        card_layout.setContentsMargins(12, 4, 8, 4)
        card_layout.setSpacing(8)

        # Left Attach / Plus Icon
        attach_btn = QPushButton("+")
        attach_btn.setObjectName("iconBtn")
        attach_btn.setCursor(Qt.PointingHandCursor)
        attach_btn.setStyleSheet("font-size: 18px; color: #8e8ea0; font-weight: bold; width: 28px; height: 28px;")
        card_layout.addWidget(attach_btn)

        # Text input field
        self.chat_input = AutoResizingTextEdit()
        self.chat_input.sendRequested.connect(self.handle_send)
        self.chat_input.textChanged.connect(self.on_input_text_changed)
        card_layout.addWidget(self.chat_input, stretch=1)

        # Send Button
        self.send_btn = QPushButton("↑")
        self.send_btn.setObjectName("sendButton")
        self.send_btn.setCursor(Qt.PointingHandCursor)
        self.send_btn.setProperty("active", "false")
        self.send_btn.clicked.connect(self.handle_send)
        card_layout.addWidget(self.send_btn)

        wrapper_layout.addWidget(input_card)

        # Footer Disclaimer
        disclaimer = QLabel("FAQ Chatbot provides responses based on the university knowledge base. Verify critical deadlines on the official portal.")
        disclaimer.setObjectName("disclaimerLbl")
        disclaimer.setAlignment(Qt.AlignCenter)
        wrapper_layout.addWidget(disclaimer)

        content_layout.addWidget(input_wrapper)
        main_layout.addWidget(self.main_content, stretch=1)

    def build_landing_page(self):
        """Builds the modern ChatGPT 'Where should we begin?' home screen."""
        self.landing_widget = QWidget()
        l_layout = QVBoxLayout(self.landing_widget)
        l_layout.setAlignment(Qt.AlignCenter)
        l_layout.setSpacing(20)

        title = QLabel("Where should we begin?")
        title.setObjectName("landingTitle")
        title.setAlignment(Qt.AlignCenter)
        l_layout.addWidget(title)

        # Grid of Suggestion Cards
        grid_container = QWidget()
        grid_layout = QVBoxLayout(grid_container)
        grid_layout.setSpacing(10)
        grid_layout.setContentsMargins(0, 0, 0, 0)

        suggestions = [
            ("🎓 How do I apply for undergraduate admissions?", "Admissions Portal application guide"),
            ("💰 How can I apply for scholarships & financial assistance?", "Financial aid options & requirements"),
            ("📍 What is the location of GIKI?", "Campus location and traveling directions"),
            ("🔄 How can I transfer to GIKI from another university?", "Transfer credits & eligibility criteria"),
        ]

        for query_text, sub in suggestions:
            btn = QPushButton(f"  {query_text}\n  {sub}")
            btn.setObjectName("suggestionCard")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked=False, q=query_text: self.submit_query(q))
            grid_layout.addWidget(btn)

        l_layout.addWidget(grid_container)
        self.chat_layout.addWidget(self.landing_widget)

    def on_input_text_changed(self):
        """Toggles send button highlight based on whether input has text."""
        has_text = bool(self.chat_input.toPlainText().strip())
        self.send_btn.setProperty("active", "true" if has_text else "false")
        self.send_btn.style().unpolish(self.send_btn)
        self.send_btn.style().polish(self.send_btn)

    def toggle_sidebar(self):
        """Expands or collapses the left navigation panel."""
        if self.sidebar.isVisible():
            self.sidebar.hide()
            self.toggle_btn_top.show()
        else:
            self.sidebar.show()
            self.toggle_btn_top.hide()

    def start_new_chat(self):
        """Clears current conversation area and presents the landing view."""
        self.current_conversation.clear()
        
        # Clear all message widgets in chat_layout
        while self.chat_layout.count():
            item = self.chat_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # Re-add landing screen
        self.build_landing_page()
        self.chat_input.clear()
        self.chat_input.setFocus()

    def handle_send(self):
        """Reads input text and processes the user query."""
        text = self.chat_input.toPlainText().strip()
        if not text:
            return
        self.chat_input.clear()
        self.submit_query(text)

    def submit_query(self, query: str):
        """Executes matching query against knowledge base and updates chat."""
        # Hide landing screen on first query
        if hasattr(self, "landing_widget") and self.landing_widget:
            self.landing_widget.hide()
            self.landing_widget.deleteLater()
            self.landing_widget = None

        # 1. Add User Message
        user_bubble = MessageBubble("user", query)
        self.chat_layout.addWidget(user_bubble)

        # 2. Query Chatbot Engine
        if not self.engine_ready:
            answer = f"⚠️ Chatbot Error: {getattr(self, 'init_error', 'Dataset not loaded')}"
            score = 0.0
        else:
            answer, score = get_response(
                query,
                self.vectorizers,
                self.matrices,
                self.faq_df,
                threshold=DEFAULT_SIMILARITY_THRESHOLD
            )

        # 3. Add Assistant Message
        bot_bubble = MessageBubble("assistant", answer, score)
        self.chat_layout.addWidget(bot_bubble)

        # 4. Save to history & sidebar
        self.record_history(query, answer, score)

        # Auto-scroll to bottom
        QTimer.singleShot(50, self.scroll_to_bottom)

    def record_history(self, query: str, answer: str, score: float):
        """Adds query to sidebar list."""
        self.chat_history.append((query, answer, score))
        
        # Format query for sidebar (truncate if long)
        display_text = query if len(query) <= 32 else query[:30] + "..."
        
        # Avoid duplicate consecutive sidebar entries
        if self.history_list.count() == 0 or self.history_list.item(0).text() != display_text:
            item = QListWidgetItem(f"💬  {display_text}")
            item.setData(Qt.UserRole, len(self.chat_history) - 1)
            self.history_list.insertItem(0, item)

    def on_history_item_clicked(self, item):
        """Loads or re-displays the selected question and answer."""
        idx = item.data(Qt.UserRole)
        if idx is not None and 0 <= idx < len(self.chat_history):
            q, a, score = self.chat_history[idx]
            
            # Reset conversation view to this item
            while self.chat_layout.count():
                it = self.chat_layout.takeAt(0)
                widget = it.widget()
                if widget:
                    widget.deleteLater()

            self.landing_widget = None
            user_bubble = MessageBubble("user", q)
            bot_bubble = MessageBubble("assistant", a, score)
            self.chat_layout.addWidget(user_bubble)
            self.chat_layout.addWidget(bot_bubble)
            QTimer.singleShot(50, self.scroll_to_bottom)

    def scroll_to_bottom(self):
        """Smoothly scrolls the message container to the bottom."""
        v_bar = self.scroll_area.verticalScrollBar()
        v_bar.setValue(v_bar.maximum())


def main():
    app = QApplication(sys.argv)
    
    # Modern font configuration
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    window = ModernChatGPTGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

"""Main desktop application window."""

import sys
import asyncio
import logging
from typing import Optional
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLineEdit, QPushButton, QLabel, QProgressBar,
    QScrollArea, QFrame, QSplitter
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QTextCursor, QPalette, QColor
from src.agents.workflow import HistoryWorkflow
from src.config import get_config

logger = logging.getLogger(__name__)


class WorkflowThread(QThread):
    """Thread for running async workflow."""
    
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, workflow: HistoryWorkflow, question: str):
        super().__init__()
        self.workflow = workflow
        self.question = question
    
    def run(self):
        """Run workflow in thread."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.workflow.process(self.question))
            loop.close()
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.config = get_config()
        self.workflow: Optional[HistoryWorkflow] = None
        self.workflow_thread: Optional[WorkflowThread] = None
        self._init_ui()
        self._init_workflow()
    
    def _init_ui(self):
        """Initialize UI components."""
        self.setWindowTitle("History Helper - Local History Assistant")
        self.setGeometry(100, 100, self.config.ui.window_width, self.config.ui.window_height)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Title
        title = QLabel("History Helper")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("Ask questions about historical events and get comprehensive, well-sourced answers")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #666; margin-bottom: 10px;")
        main_layout.addWidget(subtitle)
        
        # Input section
        input_layout = QHBoxLayout()
        self.question_input = QLineEdit()
        self.question_input.setPlaceholderText("Enter your historical question here...")
        self.question_input.setMinimumHeight(40)
        self.question_input.returnPressed.connect(self._ask_question)
        
        self.ask_button = QPushButton("Ask")
        self.ask_button.setMinimumHeight(40)
        self.ask_button.setMinimumWidth(100)
        self.ask_button.clicked.connect(self._ask_question)
        self.ask_button.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:disabled {
                background-color: #ccc;
            }
        """)
        
        input_layout.addWidget(self.question_input)
        input_layout.addWidget(self.ask_button)
        main_layout.addLayout(input_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        main_layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #666; font-style: italic;")
        main_layout.addWidget(self.status_label)
        
        # Splitter for answer and sources
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Answer section
        answer_frame = QFrame()
        answer_layout = QVBoxLayout(answer_frame)
        answer_layout.setContentsMargins(0, 0, 0, 0)
        
        answer_label = QLabel("Answer")
        answer_label_font = QFont()
        answer_label_font.setPointSize(14)
        answer_label_font.setBold(True)
        answer_label.setFont(answer_label_font)
        answer_layout.addWidget(answer_label)
        
        self.answer_display = QTextEdit()
        self.answer_display.setReadOnly(True)
        self.answer_display.setPlaceholderText("Your answer will appear here...")
        self.answer_display.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 10px;
                background-color: #f9f9f9;
            }
        """)
        answer_layout.addWidget(self.answer_display)
        
        splitter.addWidget(answer_frame)
        
        # Sources section
        sources_frame = QFrame()
        sources_layout = QVBoxLayout(sources_frame)
        sources_layout.setContentsMargins(0, 0, 0, 0)
        
        sources_label = QLabel("Sources")
        sources_label_font = QFont()
        sources_label_font.setPointSize(14)
        sources_label_font.setBold(True)
        sources_label.setFont(sources_label_font)
        sources_layout.addWidget(sources_label)
        
        self.sources_display = QTextEdit()
        self.sources_display.setReadOnly(True)
        self.sources_display.setPlaceholderText("Sources will appear here...")
        self.sources_display.setMaximumWidth(300)
        self.sources_display.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 10px;
                background-color: #f9f9f9;
                font-size: 11px;
            }
        """)
        sources_layout.addWidget(self.sources_display)
        
        splitter.addWidget(sources_frame)
        splitter.setSizes([800, 300])
        
        main_layout.addWidget(splitter)
        
        # Set theme
        if self.config.ui.theme == "dark":
            self._apply_dark_theme()
    
    def _apply_dark_theme(self):
        """Apply dark theme."""
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
        self.setPalette(palette)
    
    def _init_workflow(self):
        """Initialize workflow (lazy loading)."""
        try:
            self.status_label.setText("Initializing workflow...")
            QApplication.processEvents()
            self.workflow = HistoryWorkflow(self.config)
            self.status_label.setText("Ready. Enter a historical question to begin.")
        except Exception as e:
            logger.error(f"Failed to initialize workflow: {e}")
            self.status_label.setText(f"Error initializing: {str(e)}")
            self.ask_button.setEnabled(False)
    
    def _ask_question(self):
        """Process user question."""
        question = self.question_input.text().strip()
        if not question:
            return
        
        if self.workflow is None:
            self._init_workflow()
            if self.workflow is None:
                return
        
        # Disable input
        self.question_input.setEnabled(False)
        self.ask_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.status_label.setText("Processing your question...")
        
        # Clear previous results
        self.answer_display.clear()
        self.sources_display.clear()
        
        # Run workflow in thread
        self.workflow_thread = WorkflowThread(self.workflow, question)
        self.workflow_thread.finished.connect(self._on_workflow_finished)
        self.workflow_thread.error.connect(self._on_workflow_error)
        self.workflow_thread.start()
    
    def _on_workflow_finished(self, result: dict):
        """Handle workflow completion."""
        self.progress_bar.setVisible(False)
        self.question_input.setEnabled(True)
        self.ask_button.setEnabled(True)
        
        # Display answer
        answer = result.get("answer", "No answer generated.")
        self.answer_display.setPlainText(answer)
        
        # Display sources
        sources = result.get("sources", [])
        if sources:
            sources_text = "Sources:\n\n"
            for i, source in enumerate(sources, 1):
                title = source.get("title", "Untitled")
                url = source.get("url", "")
                score = source.get("relevance_score", 0.0)
                sources_text += f"{i}. {title}\n   {url}\n   (Relevance: {score:.2f})\n\n"
            self.sources_display.setPlainText(sources_text)
        else:
            self.sources_display.setPlainText("No sources available.")
        
        # Update status
        keywords = result.get("keywords", [])
        if keywords:
            self.status_label.setText(f"Keywords used: {', '.join(keywords)}")
        else:
            self.status_label.setText("Question processed successfully.")
    
    def _on_workflow_error(self, error: str):
        """Handle workflow error."""
        self.progress_bar.setVisible(False)
        self.question_input.setEnabled(True)
        self.ask_button.setEnabled(True)
        self.status_label.setText(f"Error: {error}")
        self.answer_display.setPlainText(f"An error occurred: {error}")
    
    def closeEvent(self, event):
        """Handle window close event."""
        if self.workflow_thread and self.workflow_thread.isRunning():
            self.workflow_thread.terminate()
            self.workflow_thread.wait()
        
        if self.workflow:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.workflow.close())
                loop.close()
            except Exception as e:
                logger.error(f"Error closing workflow: {e}")
        
        event.accept()


def main():
    """Main entry point for the application."""
    app = QApplication(sys.argv)
    app.setApplicationName("History Helper")
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()


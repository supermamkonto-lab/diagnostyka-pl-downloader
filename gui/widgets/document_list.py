"""
Document List Widget — Displays and manages document selection.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QCheckBox, QHeaderView, QAbstractItemView
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Document:
    """Reprezentacja dokumentu/badania."""
    id: str
    date: str  # YYYY-MM-DD
    name: str  # Typ badania
    file_type: str  # "pdf" lub "cda"
    size_mb: float
    checked: bool = False


class DocumentListWidget(QWidget):
    """Widget wyświetlający listę dokumentów."""

    def __init__(self):
        super().__init__()
        self.documents: List[Document] = []
        self.init_ui()

    def init_ui(self):
        """Inicjalizuj UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Tabela
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "☑",  # Checkbox
            "Data",
            "Typ badania",
            "Typ pliku",
            "Rozmiar",
            "Status"
        ])

        # Ustaw szerokości kolumn
        self.table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )
        self.table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(
            4, QHeaderView.ResizeMode.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(
            5, QHeaderView.ResizeMode.ResizeToContents
        )

        # Ustawienia tabeli
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setRowHeight(32)

        layout.addWidget(self.table)
        self.setLayout(layout)

    def add_document(self, doc: Document):
        """Dodaj dokument do listy."""
        self.documents.append(doc)
        self.refresh_table()

    def add_documents(self, docs: List[Document]):
        """Dodaj wiele dokumentów."""
        self.documents.extend(docs)
        self.refresh_table()

    def clear_documents(self):
        """Wyczyść listę dokumentów."""
        self.documents.clear()
        self.table.setRowCount(0)

    def refresh_table(self):
        """Odśwież tabelę."""
        self.table.setRowCount(len(self.documents))

        for row, doc in enumerate(self.documents):
            # Checkbox
            checkbox = QCheckBox()
            checkbox.setChecked(doc.checked)
            checkbox.stateChanged.connect(
                lambda state, r=row: self.on_checkbox_changed(r)
            )
            self.table.setCellWidget(row, 0, checkbox)

            # Data
            date_item = QTableWidgetItem(doc.date)
            self.table.setItem(row, 1, date_item)

            # Typ badania
            name_item = QTableWidgetItem(doc.name)
            self.table.setItem(row, 2, name_item)

            # Typ pliku
            type_item = QTableWidgetItem(doc.file_type.upper())
            self.table.setItem(row, 3, type_item)

            # Rozmiar
            size_item = QTableWidgetItem(f"{doc.size_mb:.1f} MB")
            self.table.setItem(row, 4, size_item)

            # Status
            status_item = QTableWidgetItem("✓ Gotów" if doc.checked else "")
            self.table.setItem(row, 5, status_item)

    def on_checkbox_changed(self, row: int):
        """Obsługuj zmianę checkboxa."""
        if row < len(self.documents):
            checkbox = self.table.cellWidget(row, 0)
            self.documents[row].checked = checkbox.isChecked()

    def select_all(self):
        """Zaznacz wszystkie."""
        for doc in self.documents:
            doc.checked = True
        self.refresh_table()

    def deselect_all(self):
        """Odznacz wszystkie."""
        for doc in self.documents:
            doc.checked = False
        self.refresh_table()

    def get_selected(self) -> List[Document]:
        """Zwróć zaznaczone dokumenty."""
        return [doc for doc in self.documents if doc.checked]

    def get_selected_count(self) -> int:
        """Zwróć liczbę zaznaczonych."""
        return len(self.get_selected())

    def get_total_count(self) -> int:
        """Zwróć liczbę wszystkich."""
        return len(self.documents)

    def get_selected_size(self) -> float:
        """Zwróć rozmiar zaznaczonych w MB."""
        return sum(doc.size_mb for doc in self.get_selected())

    def filter_by_date(self, from_date: str, to_date: str):
        """Filtruj po dacie (YYYY-MM-DD)."""
        visible = [
            i for i, doc in enumerate(self.documents)
            if from_date <= doc.date <= to_date
        ]
        # TODO: Implementuj filtrowanie widoku

    def filter_by_type(self, search_text: str):
        """Filtruj po typie badania."""
        visible = [
            i for i, doc in enumerate(self.documents)
            if search_text.lower() in doc.name.lower()
        ]
        # TODO: Implementuj filtrowanie widoku

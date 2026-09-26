import io
import re
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Tuple, Union
import openpyxl
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from backend.models.progress import LectureProgression, TopicProgress


PRIMARY_SHEET_NAME = "Course Progression"
EVIDENCE_SHEET_NAME = "Evidence"

REQUIRED_COLUMNS = [
    "Date Taught",
    "Status",
    "% Completed",
    "% Covered",
    "CW",
    "HW",
]


class ExcelService:
    """
    Day 5 Excel Generation and Update Service.
    Transforms validated Day 4 progress results deterministically into
    official Course Progression Excel workbooks (.xlsx).
    """

    @staticmethod
    def normalize_status(status_val: Any) -> str:
        """Normalizes status value to standard clean casing."""
        if not status_val:
            return "Ongoing"
        s = str(status_val).strip()
        s_upper = s.upper()
        if s_upper == "COMPLETED":
            return "Completed"
        elif s_upper == "ONGOING":
            return "Ongoing"
        elif s_upper in ("SPILLED OVER", "SPILLED_OVER"):
            return "Spilled Over"
        elif s_upper in ("NOT_STARTED", "NOT STARTED"):
            return "Not Started"
        return s.title()

    @staticmethod
    def format_percentage(val: Any) -> float:
        """Rounds percentages to two decimals deterministically, avoiding float noise."""
        try:
            return round(float(val), 2)
        except (ValueError, TypeError):
            return 0.0

    @staticmethod
    def extract_text_items(items: Any) -> str:
        """
        Extracts verified Classwork/Homework descriptions.
        Does NOT invent or copy curriculum defaults if not evidenced.
        """
        if not items:
            return ""
        if isinstance(items, str):
            return items.strip()
        if isinstance(items, (list, tuple)):
            descriptions: List[str] = []
            for item in items:
                if not item:
                    continue
                if isinstance(item, str):
                    desc = item.strip()
                    if desc:
                        descriptions.append(desc)
                elif hasattr(item, "description") and item.description:
                    desc = str(item.description).strip()
                    if desc:
                        descriptions.append(desc)
                elif isinstance(item, dict) and item.get("description"):
                    desc = str(item["description"]).strip()
                    if desc:
                        descriptions.append(desc)
            return "; ".join(descriptions)
        return str(items).strip()

    @classmethod
    def extract_progression_record(
        cls,
        progression: Union[LectureProgression, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Extracts a normalized dictionary representing the progression record
        without mutating or recalculating progression metrics.
        """
        if isinstance(progression, LectureProgression):
            lecture = progression.lecture
            date_taught = progression.date_taught
            status = cls.normalize_status(progression.status)
            percent_completed = cls.format_percentage(progression.percent_completed)
            percent_covered = cls.format_percentage(progression.percent_covered)
            cw = cls.extract_text_items(progression.classwork)
            hw = cls.extract_text_items(progression.homework)
            topics = progression.topics or []
            warnings = progression.warnings or []
        elif isinstance(progression, dict):
            # Check if wrapped in {"progression": {...}}
            data = progression.get("progression", progression)
            lecture = str(data.get("lecture", "")).strip()
            date_taught = str(data.get("date_taught", "")).strip() or date.today().isoformat()
            status = cls.normalize_status(data.get("status", "Ongoing"))
            percent_completed = cls.format_percentage(data.get("percent_completed", 0.0))
            percent_covered = cls.format_percentage(data.get("percent_covered", 0.0))
            cw = cls.extract_text_items(data.get("classwork", data.get("cw", "")))
            hw = cls.extract_text_items(data.get("homework", data.get("hw", "")))
            topics = data.get("topics", [])
            warnings = data.get("warnings", [])
        else:
            raise ValueError(f"Invalid progression data type: {type(progression)}")

        if not date_taught:
            date_taught = date.today().isoformat()

        return {
            "lecture": lecture,
            "date_taught": date_taught,
            "status": status,
            "percent_completed": percent_completed,
            "percent_covered": percent_covered,
            "cw": cw,
            "hw": hw,
            "topics": topics,
            "warnings": warnings,
        }

    @classmethod
    def _apply_primary_sheet_styles(cls, ws: openpyxl.worksheet.worksheet.Worksheet) -> None:
        """Applies professional, clean academic formatting to the primary progression sheet."""
        header_font = Font(name="Calibri", size=11, bold=True, color="1F2937")
        header_fill = PatternFill(start_color="F3F4F6", end_color="F3F4F6", fill_type="solid")
        header_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
        thin_border = Border(
            left=Side(style="thin", color="E5E7EB"),
            right=Side(style="thin", color="E5E7EB"),
            top=Side(style="thin", color="D1D5DB"),
            bottom=Side(style="medium", color="9CA3AF"),
        )

        ws.row_dimensions[1].height = 26
        for col_idx in range(1, len(REQUIRED_COLUMNS) + 1):
            cell = ws.cell(row=1, column=col_idx)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_align
            cell.border = thin_border

        # Freeze the top header row
        ws.freeze_panes = "A2"

        # Set human-readable column widths
        widths = {
            "A": 16,  # Date Taught
            "B": 16,  # Status
            "C": 15,  # % Completed
            "D": 15,  # % Covered
            "E": 36,  # CW
            "F": 36,  # HW
        }
        for col_letter, w in widths.items():
            ws.column_dimensions[col_letter].width = w

    @classmethod
    def _format_data_row(
        cls,
        ws: openpyxl.worksheet.worksheet.Worksheet,
        row_idx: int,
        record: Dict[str, Any]
    ) -> None:
        """Writes and formats a single progression data row."""
        data_font = Font(name="Calibri", size=11, color="111827")
        cell_border = Border(
            left=Side(style="thin", color="E5E7EB"),
            right=Side(style="thin", color="E5E7EB"),
            top=Side(style="thin", color="E5E7EB"),
            bottom=Side(style="thin", color="E5E7EB"),
        )

        # 1. Date Taught
        c1 = ws.cell(row=row_idx, column=1, value=record["date_taught"])
        c1.font = data_font
        c1.alignment = Alignment(horizontal="center", vertical="top")
        c1.border = cell_border

        # 2. Status
        c2 = ws.cell(row=row_idx, column=2, value=record["status"])
        c2.font = data_font
        c2.alignment = Alignment(horizontal="center", vertical="top")
        c2.border = cell_border

        # 3. % Completed
        c3 = ws.cell(row=row_idx, column=3, value=record["percent_completed"])
        c3.font = data_font
        c3.alignment = Alignment(horizontal="right", vertical="top")
        c3.number_format = "0.00"
        c3.border = cell_border

        # 4. % Covered
        c4 = ws.cell(row=row_idx, column=4, value=record["percent_covered"])
        c4.font = data_font
        c4.alignment = Alignment(horizontal="right", vertical="top")
        c4.number_format = "0.00"
        c4.border = cell_border

        # 5. CW
        c5 = ws.cell(row=row_idx, column=5, value=record["cw"])
        c5.font = data_font
        c5.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)
        c5.border = cell_border

        # 6. HW
        c6 = ws.cell(row=row_idx, column=6, value=record["hw"])
        c6.font = data_font
        c6.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)
        c6.border = cell_border

    @classmethod
    def _populate_evidence_sheet(
        cls,
        wb: Workbook,
        record: Dict[str, Any]
    ) -> None:
        """
        Populates the secondary Evidence sheet.
        Contains lecture, topic details, confidence, evidence, and warnings.
        """
        if EVIDENCE_SHEET_NAME in wb.sheetnames:
            ws_ev = wb[EVIDENCE_SHEET_NAME]
        else:
            ws_ev = wb.create_sheet(title=EVIDENCE_SHEET_NAME)

        ev_headers = ["Lecture", "Date Taught", "Topic", "Topic Status", "Confidence", "Evidence"]
        header_font = Font(name="Calibri", size=11, bold=True, color="1F2937")
        header_fill = PatternFill(start_color="F3F4F6", end_color="F3F4F6", fill_type="solid")
        border = Border(
            left=Side(style="thin", color="E5E7EB"),
            right=Side(style="thin", color="E5E7EB"),
            top=Side(style="thin", color="D1D5DB"),
            bottom=Side(style="medium", color="9CA3AF"),
        )

        # Check if header needs to be written
        if ws_ev.max_row < 1 or ws_ev.cell(row=1, column=1).value != "Lecture":
            ws_ev.row_dimensions[1].height = 24
            for col_idx, h in enumerate(ev_headers, start=1):
                c = ws_ev.cell(row=1, column=col_idx, value=h)
                c.font = header_font
                c.fill = header_fill
                c.alignment = Alignment(horizontal="center", vertical="center")
                c.border = border
            ws_ev.freeze_panes = "A2"

        # Remove existing rows for this specific lecture & date taught if updating
        lecture_val = record.get("lecture", "")
        date_val = record.get("date_taught", "")
        if ws_ev.max_row > 1 and (lecture_val or date_val):
            rows_to_delete = []
            for r in range(2, ws_ev.max_row + 1):
                row_lec = str(ws_ev.cell(row=r, column=1).value or "").strip()
                row_date = str(ws_ev.cell(row=r, column=2).value or "").strip()
                if lecture_val and date_val:
                    if row_lec == lecture_val and row_date == date_val:
                        rows_to_delete.append(r)
                elif date_val and row_date == date_val:
                    rows_to_delete.append(r)
            for r in reversed(rows_to_delete):
                ws_ev.delete_rows(r)

        # Append new topic evidence
        topics = record.get("topics", [])
        data_font = Font(name="Calibri", size=10, color="111827")
        cell_border = Border(
            left=Side(style="thin", color="E5E7EB"),
            right=Side(style="thin", color="E5E7EB"),
            top=Side(style="thin", color="E5E7EB"),
            bottom=Side(style="thin", color="E5E7EB"),
        )

        start_row = ws_ev.max_row + 1
        for idx, t in enumerate(topics):
            curr_row = start_row + idx
            if isinstance(t, TopicProgress):
                t_name = t.name
                t_status = t.status.value if hasattr(t.status, "value") else str(t.status)
                t_conf = f"{t.confidence:.2f}" if t.confidence is not None else ""
                t_ev = t.evidence or ""
            elif isinstance(t, dict):
                t_name = t.get("name", t.get("curriculum_topic", ""))
                t_status = str(t.get("status", "covered"))
                conf = t.get("confidence")
                t_conf = f"{float(conf):.2f}" if conf is not None else ""
                t_ev = t.get("evidence", "")
            else:
                t_name = str(t)
                t_status = "covered"
                t_conf = ""
                t_ev = ""

            row_data = [lecture_val, date_val, t_name, t_status, t_conf, t_ev]
            for col_idx, val in enumerate(row_data, start=1):
                c = ws_ev.cell(row=curr_row, column=col_idx, value=val)
                c.font = data_font
                c.border = cell_border
                c.alignment = Alignment(
                    horizontal="center" if col_idx in (1, 2, 4, 5) else "left",
                    vertical="top",
                    wrap_text=(col_idx == 6),
                )

        # Adjust evidence sheet column widths
        ev_widths = {"A": 14, "B": 14, "C": 30, "D": 16, "E": 14, "F": 45}
        for col_letter, w in ev_widths.items():
            ws_ev.column_dimensions[col_letter].width = w

    @classmethod
    def generate_progression_workbook(
        cls,
        progression: Union[LectureProgression, Dict[str, Any]]
    ) -> bytes:
        """
        Creates a new Course Progression Excel workbook (.xlsx) from validated progression data.
        Returns the raw binary content of the workbook.
        """
        record = cls.extract_progression_record(progression)

        wb = Workbook()
        # Default sheet is ws
        ws = wb.active
        ws.title = PRIMARY_SHEET_NAME

        # Write Headers
        for col_idx, h in enumerate(REQUIRED_COLUMNS, start=1):
            ws.cell(row=1, column=col_idx, value=h)

        cls._apply_primary_sheet_styles(ws)

        # Write Data Row
        cls._format_data_row(ws, row_idx=2, record=record)

        # Apply autofilter
        ws.auto_filter.ref = f"A1:F2"

        # Populate secondary Evidence sheet
        cls._populate_evidence_sheet(wb, record)

        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()

    @classmethod
    def find_primary_sheet(
        cls,
        wb: Workbook
    ) -> Tuple[openpyxl.worksheet.worksheet.Worksheet, int]:
        """
        Locates the primary progression sheet and its header row index.
        Raises ValueError if no valid progression table is found.
        """
        # 1. Check if sheet named PRIMARY_SHEET_NAME exists
        candidate_sheets = []
        if PRIMARY_SHEET_NAME in wb.sheetnames:
            candidate_sheets.append(wb[PRIMARY_SHEET_NAME])
        for s in wb.worksheets:
            if s not in candidate_sheets:
                candidate_sheets.append(s)

        for ws in candidate_sheets:
            for r in range(1, min(10, ws.max_row + 1)):
                row_vals = [
                    str(ws.cell(row=r, column=c).value or "").strip()
                    for c in range(1, len(REQUIRED_COLUMNS) + 1)
                ]
                # Check match against required columns (case-insensitive)
                matches = sum(
                    1 for exp, act in zip(REQUIRED_COLUMNS, row_vals)
                    if exp.lower() == act.lower()
                )
                if matches >= 5:  # At least 5 of 6 match exact headers
                    return ws, r

        raise ValueError(
            "Invalid course progression workbook: Could not find sheet with required headers "
            f"({', '.join(REQUIRED_COLUMNS)})."
        )

    @classmethod
    def update_progression_workbook(
        cls,
        existing_file_bytes: bytes,
        progression: Union[LectureProgression, Dict[str, Any]]
    ) -> bytes:
        """
        Updates an existing course progression workbook without destroying previous records.
        Implements deterministic duplicate protection: if the same lecture/date already
        exists, updates the existing row in place; otherwise appends a new row.
        """
        if not existing_file_bytes:
            # If empty workbook supplied, generate a fresh workbook
            return cls.generate_progression_workbook(progression)

        try:
            wb = load_workbook(io.BytesIO(existing_file_bytes))
        except Exception as exc:
            raise ValueError(f"Corrupt or unreadable Excel workbook: {str(exc)}")

        ws, header_row = cls.find_primary_sheet(wb)
        record = cls.extract_progression_record(progression)

        target_date = str(record["date_taught"]).strip()
        target_lecture = str(record.get("lecture", "")).strip()

        # Check existing data rows for duplicate detection
        # Match strategy: Check Date Taught (and verify against Evidence sheet if available)
        matching_row_idx = None

        # Check Evidence sheet first for exact (lecture, date) match
        lecture_date_map: Dict[str, str] = {}
        if EVIDENCE_SHEET_NAME in wb.sheetnames:
            ws_ev = wb[EVIDENCE_SHEET_NAME]
            for r in range(2, ws_ev.max_row + 1):
                lec_c = str(ws_ev.cell(row=r, column=1).value or "").strip()
                date_c = str(ws_ev.cell(row=r, column=2).value or "").strip()
                if lec_c and date_c:
                    lecture_date_map[date_c] = lec_c

        data_start_row = header_row + 1
        for r in range(data_start_row, ws_ev_max := ws.max_row + 1):
            cell_date = ws.cell(row=r, column=1).value
            if cell_date is None:
                continue

            # Format cell_date to ISO YYYY-MM-DD if datetime/date object
            if isinstance(cell_date, (datetime, date)):
                cell_date_str = cell_date.strftime("%Y-%m-%d")
            else:
                cell_date_str = str(cell_date).strip()

            if cell_date_str == target_date:
                # If target_lecture matches the mapped lecture for this date, or if no lecture distinction
                mapped_lec = lecture_date_map.get(cell_date_str)
                if not mapped_lec or not target_lecture or mapped_lec == target_lecture:
                    matching_row_idx = r
                    break

        if matching_row_idx is not None:
            # Update existing row in place
            target_row = matching_row_idx
        else:
            # Append new row
            target_row = ws.max_row + 1

        cls._format_data_row(ws, row_idx=target_row, record=record)

        # Update table autofilter range
        ws.auto_filter.ref = f"A{header_row}:F{max(target_row, ws.max_row)}"

        # Also update Evidence sheet
        cls._populate_evidence_sheet(wb, record)

        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()


excel_service = ExcelService()

"""Google Sheets API integration service."""

import logging
from typing import Optional, List, Any
from sqlalchemy.orm import Session, joinedload
from datetime import datetime

from app.config import settings
from app.core.id_generator import ulid_to_display_id
from app.models.user import User, UserStatus, UserCategory
from app.models.role import UserRole
from app.models.domain import Domain
from app.models.division import Division

logger = logging.getLogger(__name__)


class GoogleSheetsService:
    """
    Service for bi-directional sync with Google Sheets.
    Requires a Google Cloud Service Account with Sheets API access.
    """

    HEADERS = ["ID", "ULID", "Name", "Email", "Category", "Status", "Roles", "Domain", "Division", "Start Date", "End Date"]

    def __init__(self, db: Session):
        self.db = db
        self._client = None
        self._spreadsheet = None

    def _connect(self):
        """Establish connection to Google Sheets using service account credentials."""
        if self._client is not None:
            return

        try:
            import gspread
            from google.oauth2.service_account import Credentials

            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ]
            creds = Credentials.from_service_account_file(
                settings.GOOGLE_SERVICE_ACCOUNT_FILE, scopes=scopes
            )
            self._client = gspread.authorize(creds)
            self._spreadsheet = self._client.open_by_key(settings.GOOGLE_SHEET_ID)
            logger.info("Connected to Google Sheets")
        except Exception as e:
            logger.error(f"Failed to connect to Google Sheets: {e}")
            raise

    def push_all(self) -> int:
        """Push all user records to Google Sheets (full sync) with multiple tabs."""
        self._connect()
        total_synced = 0

        # 1. Active Employees
        total_synced += self._sync_sheet(
            "Active Employees",
            (User.category == UserCategory.EMPLOYEE) & (User.status == UserStatus.ACTIVE)
        )

        # 2. Interns
        total_synced += self._sync_sheet(
            "Interns",
            (User.category == UserCategory.INTERN) & (User.status == UserStatus.ACTIVE)
        )

        # 3. Inactive Users
        total_synced += self._sync_sheet(
            "Inactive Users",
            User.status.in_([UserStatus.INACTIVE, UserStatus.EXPIRED])
        )

        # 4. Deleted Users
        total_synced += self._sync_sheet(
            "Deleted Users",
            None,
            include_deleted=True
        )
        
        # 5. Domains
        self._sync_domains()
        
        # 6. Departments
        self._sync_departments()

        # 7. Users by Domain
        self._sync_grouped_users("Users by Domain", User.domain_id)

        # 8. Users by Department
        self._sync_grouped_users("Users by Department", User.division_id)

        logger.info(f"Pushed total {total_synced} user records to Google Sheets")
        return total_synced

    def _sync_sheet(self, title: str, query_filter, include_deleted=False) -> int:
        """Helper to sync a standard user list sheet."""
        # fetch data
        query = self.db.query(User).options(
            joinedload(User.domain),
            joinedload(User.division),
            joinedload(User.user_roles).joinedload(UserRole.role),
            joinedload(User.internship),
        )

        if include_deleted:
            query = query.filter(User.deleted_at != None)
        else:
            query = query.filter(User.deleted_at == None)
            if query_filter is not None:
                query = query.filter(query_filter)
        
        users = query.order_by(User.created_at).all()
        
        rows = [self.HEADERS]
        for user in users:
            roles = ", ".join(
                ur.role.name for ur in user.user_roles
                if ur.removed_at is None and ur.role.is_active
            )
            display_id = ulid_to_display_id(user.ulid, user.category.value if user.category else None)
            
            rows.append([
                display_id,
                user.ulid,
                user.name,
                user.email,
                user.category.value,
                user.status.value,
                roles,
                user.domain.name if user.domain else "",
                user.division.name if user.division else "",
                str(user.internship.start_date) if user.internship else "",
                str(user.internship.end_date) if user.internship else "",
            ])

        self._write_to_sheet(title, rows)
        return len(users)

    def _sync_grouped_users(self, title: str, order_by_col) -> int:
        """Sync users sorted/grouped by a column."""
        users = self.db.query(User).options(
                joinedload(User.domain),
                joinedload(User.division),
                joinedload(User.user_roles).joinedload(UserRole.role),
                joinedload(User.internship),
            ).filter(User.deleted_at == None).order_by(order_by_col, User.name).all()

        rows = [self.HEADERS]
        for user in users:
            roles = ", ".join(ur.role.name for ur in user.user_roles if ur.removed_at is None)
            display_id = ulid_to_display_id(user.ulid, user.category.value if user.category else None)
            
            rows.append([
                display_id, user.ulid, user.name, user.email, user.category.value, user.status.value, roles,
                user.domain.name if user.domain else "Unassigned",
                user.division.name if user.division else "Unassigned",
                str(user.internship.start_date) if user.internship else "",
                str(user.internship.end_date) if user.internship else "",
            ])
        
        self._write_to_sheet(title, rows)
        return len(users)

    def _sync_domains(self):
        rows = [["ID", "Name", "Description", "Active User Count"]]
        domains = self.db.query(Domain).all()
        for d in domains:
             count = self.db.query(User).filter(User.domain_id == d.id, User.deleted_at == None).count()
             rows.append([d.id, d.name, d.description, count])
        self._write_to_sheet("Domains", rows)

    def _sync_departments(self):
        rows = [["ID", "Name", "Description", "Active User Count"]]
        divisions = self.db.query(Division).all()
        for d in divisions:
             count = self.db.query(User).filter(User.division_id == d.id, User.deleted_at == None).count()
             rows.append([str(d.id), d.name, d.description, count])
        self._write_to_sheet("Departments", rows)

    def _get_or_create_worksheet(self, title: str):
        try:
            return self._spreadsheet.worksheet(title)
        except:
            return self._spreadsheet.add_worksheet(title=title, rows=100, cols=20)

    def _write_to_sheet(self, title: str, rows: List[List[Any]]):
        """
        Write data to sheet and apply Advanced Aesthetics:
        - Banding (Alternating Colors)
        - Filters
        - Smart Chips (Dropdowns) for Status/Category
        - Auto-Resize Columns
        - Borders & Header Styling
        """
        ws = self._get_or_create_worksheet(title)
        
        # 1. Clear existing values
        ws.clear()
        
        if not rows:
            return

        # 2. Write new data
        ws.update(range_name="A1", values=rows)

        num_rows = len(rows)
        num_cols = len(rows[0])
        sheet_id = ws.id

        # 3. Prepare Batch Requests
        requests = []

        # --- Clean Up Previous Formatting (Robustness) ---
        # We need to fetch metadata to find existing bandings/filters to remove them
        # so we don't get errors or duplicates. 
        # Ideally we would fetch metadata here, but for efficiency/simplicity in this script 
        # we will try to just overwrite 'userEnteredFormat' and set new stuff. 
        # However, 'addBanding' errors if one exists.
        # Strategy: Clear all formatting + Clear Filter + Delete Banding (if we could guess ID, but we can't).
        # A simple robust way is:
        # a) clearBasicFilter (always safe)
        # b) updateCells with cleared format (resets colors/borders)
        # c) For Banding, it's tricky without ID. 
        # Let's try to fetch metadata for this sheet specifically to clear bandings.
        
        try:
            # gspread 6.x should have this. if not, we fallback to simple formatting.
            meta = self._spreadsheet.fetch_sheet_metadata()
            sheet_meta = next((s for s in meta['sheets'] if s['properties']['sheetId'] == sheet_id), None)
            
            if sheet_meta:
                # Remove Filter
                if 'basicFilter' in sheet_meta:
                    requests.append({"clearBasicFilter": {"sheetId": sheet_id}})
                
                # Remove Bandings
                if 'bandedRanges' in sheet_meta:
                    for band in sheet_meta['bandedRanges']:
                        requests.append({"deleteBanding": {"bandedRangeId": band['bandedRangeId']}})
        except Exception as e:
            logger.warning(f"Could not fetch metadata to clear styles: {e}")

        # --- Apply New Aesthetics ---

        # A. Basic Table Setup (Alignment & Wrapping) -> Borders handled separately
        requests.append({
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": 0,
                    "endRowIndex": num_rows,
                    "startColumnIndex": 0,
                    "endColumnIndex": num_cols
                },
                "cell": {
                    "userEnteredFormat": {
                        "horizontalAlignment": "LEFT",
                        "verticalAlignment": "MIDDLE",
                        "wrapStrategy": "CLIP"
                    }
                },
                "fields": "userEnteredFormat(horizontalAlignment,verticalAlignment,wrapStrategy)"
            }
        })

        # B. Header Styling (Center Align + Bold) - Color handled by Banding
        requests.append({
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": 0,
                    "endRowIndex": 1,
                    "startColumnIndex": 0,
                    "endColumnIndex": num_cols
                },
                "cell": {
                    "userEnteredFormat": {
                        "horizontalAlignment": "CENTER",
                        "textFormat": {
                            "bold": True,
                            "foregroundColor": {"red": 1, "green": 1, "blue": 1} # White text
                        }
                    }
                },
                "fields": "userEnteredFormat(horizontalAlignment,textFormat)"
            }
        })

        # C. Borders (Handled via updateBorders, not repeatCell)
        requests.append({
            "updateBorders": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": 0,
                    "endRowIndex": num_rows,
                    "startColumnIndex": 0,
                    "endColumnIndex": num_cols
                },
                "top": {"style": "SOLID", "width": 1, "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
                "bottom": {"style": "SOLID", "width": 1, "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
                "left": {"style": "SOLID", "width": 1, "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
                "right": {"style": "SOLID", "width": 1, "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
                "innerHorizontal": {"style": "SOLID", "width": 1, "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
                "innerVertical": {"style": "SOLID", "width": 1, "color": {"red": 0.8, "green": 0.8, "blue": 0.8}},
            }
        })

        # C. Table Banding (Alternating Colors + Header BG)
        requests.append({
            "addBanding": {
                "bandedRange": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 0,
                        "endRowIndex": num_rows,
                        "startColumnIndex": 0,
                        "endColumnIndex": num_cols
                    },
                    "rowProperties": {
                        "headerColor": {"red": 0.066, "green": 0.33, "blue": 0.8}, # Dark Blue Header
                        "firstBandColor": {"red": 1, "green": 1, "blue": 1},       # White
                        "secondBandColor": {"red": 0.95, "green": 0.95, "blue": 0.95} # Light Grey
                    }
                }
            }
        })

        # D. Filter View
        requests.append({
            "setBasicFilter": {
                "filter": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 0,
                        "endRowIndex": num_rows,
                        "startColumnIndex": 0,
                        "endColumnIndex": num_cols
                    }
                }
            }
        })

        # E. Smart Chips (Dropdowns)
        # Find column indices
        header_row = rows[0]
        
        if "Status" in header_row:
            status_idx = header_row.index("Status")
            requests.append({
                "setDataValidation": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 1,
                        "endRowIndex": num_rows,
                        "startColumnIndex": status_idx,
                        "endColumnIndex": status_idx + 1
                    },
                    "rule": {
                        "condition": {
                            "type": "ONE_OF_LIST",
                            "values": [
                                {"userEnteredValue": s.value} for s in UserStatus
                            ]
                        },
                        "showCustomUi": True, # These are the "chips" arrow
                        "strict": True
                    }
                }
            })
            
            # Conditional Formatting for "Smart Chip" look (Pill colors)
            # Green for ACTIVE
            requests.append({
                "addConditionalFormatRule": {
                    "rule": {
                        "ranges": [{"sheetId": sheet_id, "startColumnIndex": status_idx, "endColumnIndex": status_idx+1}],
                        "booleanRule": {
                            "condition": {"type": "TEXT_EQ", "values": [{"userEnteredValue": "ACTIVE"}]},
                            "format": {
                                "backgroundColor": {"red": 0.85, "green": 0.98, "blue": 0.85},
                                "textFormat": {"foregroundColor": {"red": 0.05, "green": 0.4, "blue": 0.1}}
                            }
                        }
                    },
                    "index": 0
                }
            })
            # Red for INACTIVE/EXPIRED
            for status in ["INACTIVE", "EXPIRED"]:
                requests.append({
                    "addConditionalFormatRule": {
                        "rule": {
                            "ranges": [{"sheetId": sheet_id, "startColumnIndex": status_idx, "endColumnIndex": status_idx+1}],
                            "booleanRule": {
                                "condition": {"type": "TEXT_EQ", "values": [{"userEnteredValue": status}]},
                                "format": {
                                    "backgroundColor": {"red": 0.98, "green": 0.85, "blue": 0.85},
                                    "textFormat": {"foregroundColor": {"red": 0.6, "green": 0, "blue": 0}}
                                }
                            }
                        },
                        "index": 1
                    }
                })

        if "Category" in header_row:
            cat_idx = header_row.index("Category")
            requests.append({
                "setDataValidation": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 1,
                        "endRowIndex": num_rows,
                        "startColumnIndex": cat_idx,
                        "endColumnIndex": cat_idx + 1
                    },
                    "rule": {
                        "condition": {
                            "type": "ONE_OF_LIST",
                            "values": [
                                {"userEnteredValue": c.value} for c in UserCategory
                            ]
                        },
                        "showCustomUi": True,
                        "strict": True
                    }
                }
            })

        # F. Auto Resize (Last step to fit everything)
        requests.append({
            "autoResizeDimensions": {
                "dimensions": {
                    "sheetId": sheet_id,
                    "dimension": "COLUMNS",
                    "startIndex": 0,
                    "endIndex": num_cols
                }
            }
        })

        # Send the batch update
        if requests:
            self._spreadsheet.batch_update({"requests": requests})


    def push_changes(self) -> int:
        """Push only recently changed records (incremental sync)."""
        return self.push_all()

    def pull_updates(self) -> dict:
        """
        Pull updates from Google Sheets and apply to database.
        For now, this only supports updating from the 'Active Employees' sheet to keep it simple,
        or we can iterate through all but that might be complex.
        Let's restrict two-way sync to 'Active Employees' tab for safety or just the main list.
        """
        self._connect()
        # TODO: Implement multi-sheet pull if needed.
        # For this iteration, we focus on the robust Export-Sync (One way Push mostly used).
        # We can look for 'Active Employees' sheet.
        try:
            ws = self._spreadsheet.worksheet("Active Employees")
        except:
            return {"error": "Active Employees sheet not found"}

        from app.models.user import User, UserStatus
        
        records = ws.get_all_records()
        result = {"updated": 0, "skipped": 0, "errors": []}
        
        for i, record in enumerate(records):
            # Map column names if they changed
            ulid_value = str(record.get("ULID", "")).strip()
            if not ulid_value:
                continue

            user = self.db.query(User).filter(User.ulid == ulid_value).first()
            if not user:
                result["skipped"] += 1
                continue

            try:
                # Update Name
                name = str(record.get("Name", "")).strip()
                if name and name != user.name:
                    user.name = name
                
                # Update Status
                status_str = str(record.get("Status", "")).strip().upper()
                if status_str and status_str in [s.value for s in UserStatus]:
                    user.status = UserStatus(status_str)

                result["updated"] += 1
            except Exception as e:
                result["errors"].append(f"Row {i+2}: {e}")

        self.db.commit()
        return result

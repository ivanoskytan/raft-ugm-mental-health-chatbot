from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from azure.storage.blob import BlobServiceClient
from config.config import Settings
import io

settings = Settings.load()
class FileService:

    CONTAINER_NAME = "assessments"

    @staticmethod
    def save_into_excel(assessment_map, chat_id):
        try: 
            wb = Workbook()

            default_sheet = wb.active
            wb.remove(default_sheet)

            header_font = Font(bold=True, color="FFFFFF")
            header_fill = PatternFill(start_color="4CAF50", end_color="4CAF50", fill_type="solid")
            center_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
            left_align = Alignment(horizontal="left", vertical="center", wrap_text=True)

            thin_border = Border(
                left=Side(style="thin"),
                right=Side(style="thin"),
                top=Side(style="thin"),
                bottom=Side(style="thin"),
            )

            for section_data in assessment_map:
                section_name = section_data["section"]
                questions = section_data["questions"]

                sheet = wb.create_sheet(title=section_name)

                headers = ["No.", "Pertanyaan", "Skor"]

                sheet.append(headers)

                for col in range(1, len(headers) + 1):
                    cell = sheet.cell(row=1, column=col)
                    cell.font = header_font
                    cell.fill = header_fill
                    cell.alignment = center_align
                    cell.border = thin_border

                for idx, q in enumerate(questions, start=1):
                    sheet.append([
                        idx,
                        q["original_question"],
                        q["score"]
                    ])

                for row in sheet.iter_rows(min_row=2, max_row=sheet.max_row):
                    for cell in row:
                        cell.border = thin_border
                        if cell.column == 1 or cell.column == 3:
                            cell.alignment = center_align
                        else:
                            cell.alignment = left_align

                sheet.column_dimensions["A"].width = 6
                sheet.column_dimensions["B"].width = 60
                sheet.column_dimensions["C"].width = 10

            file_name = f"Asesmen Kesehatan Mental_{chat_id}.xlsx"

            excel_file = io.BytesIO()
            wb.save(excel_file)
            excel_file.seek()

            blob_service_client = BlobServiceClient.from_connection_string(settings.STORAGE_CONN_STR)
            blob_client = blob_service_client.get_blob_client(container=FileService.CONTAINER_NAME, blob=file_name)

            blob_client.upload_blob(excel_file, overwrite=True)

            return True, blob_client.url
        
        except Exception as e:
            return False, f"[FileService]: Failed to create Excel {str(e)}"


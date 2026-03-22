import smtplib
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email import encoders
from config.config import Settings

import os

class EmailService:

    @staticmethod
    def send_gmail(file_path, recipient):
        try: 
            msg = MIMEMultipart()
            settings = Settings.load()

            html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif;">
                    <h2 style="color:#4CAF50;">Hasil Asesmen Kesehatan Mental</h2>
                    <p>Halo,</p>
                    <p>
                        Terima kasih telah menggunakan layanan chatbot kesehatan mental.
                    </p>
                    <p>
                        Hasil asesmen Anda telah tersedia dan terlampir dalam email ini.
                    </p>

                    <p>
                        <b>File:</b> {os.path.basename(file_path)}
                    </p>

                    <br>
                    <p>
                        Mohon gunakan hasil ini sebagai referensi awal, dan pertimbangkan
                        untuk berkonsultasi dengan profesional jika diperlukan.
                    </p>

                    <br>
                    <p>Salam,<br>
                    Chatbot Kesehatan Mental UGM</p>
                </body>
            </html>
            """
            
            msg['Subject'] = "Hasil Asesmen Chatbot Kesehatan Mental UGM"
            msg['From'] = settings.MAIL_DEFAULT_SENDER
            msg['To'] = recipient
            msg.attach(MIMEText(html_content, "html"))

            if file_path and os.path.exists(file_path):
                with open(file_path, "rb") as f:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(f.read())

                encoders.encode_base64(part)
                filename = os.path.basename(file_path)
                part.add_header(
                    "Content-Disposition",
                    f'attachment; filename="{filename}"'
                )

                msg.attach(part)

            with smtplib.SMTP_SSL(settings.MAIL_SERVER, settings.MAIL_PORT) as smtp_server:
                smtp_server.login(settings.MAIL_DEFAULT_SENDER, settings.MAIL_PASSWORD)
                smtp_server.sendmail(settings.MAIL_DEFAULT_SENDER, recipient, msg.as_string())
            
            return True, None
        
        except smtplib.SMTPAuthenticationError:
            return False, "[EmailService]: Authentication Failed (check email/password)"
        
        except smtplib.SMTPException as e:
            return False, f"[EmailService]: SMTP error - {str(e)}"
        
        except Exception as e:
            return False, f"[EmailSerivce]: Unexpected error - {str(e)}"
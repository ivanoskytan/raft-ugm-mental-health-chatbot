import smtplib
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email import encoders
from config.config import Settings

import os

class EmailService:

    @staticmethod
    def send_gmail(file_content, file_url, file_name, recipient):
        try: 
            msg = MIMEMultipart()
            settings = Settings.load()

            html_content = f"""
            <html>
                <head>
                    <meta charset="UTF-8">
                    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
                </head>
                <body style="background-color: #0d0f12; margin: 0; padding: 40px 16px; font-family: 'Plus Jakarta Sans', Arial, sans-serif; color: #e5e7eb; -webkit-text-size-adjust: 100%;">
                    <div style="background: #12151b; border: 1px solid #1e222b; width: 100%; max-width: 500px; margin: 0 auto; padding: 2.5rem 2rem; border-radius: 16px; box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3); box-sizing: border-box;">
                        
                        <h2 style="font-size: 1.4rem; font-weight: 700; text-align: center; margin: 0 0 1.5rem 0; color: #ffffff; line-height: 1.4;">
                            Hasil Asesmen Kesehatan Mental
                        </h2>
                        
                        <p style="font-size: 0.95rem; font-weight: 500; color: #e5e7eb; margin-bottom: 1rem; line-height: 1.5;">
                            Halo,
                        </p>
                        <p style="font-size: 0.95rem; color: #9ca3af; margin-bottom: 1.25rem; line-height: 1.6;">
                            Terima kasih telah menggunakan layanan chatbot kesehatan mental kami.
                        </p>
                        <p style="font-size: 0.95rem; color: #9ca3af; margin-bottom: 1.5rem; line-height: 1.6;">
                            Hasil asesmen Anda telah selesai diproses dan <strong style="color: #ffffff; font-weight: 600;">telah kami lampirkan dalam bentuk file Excel</strong> pada email ini. Silakan unduh lampiran di bawah untuk melihat detail skor per bagian.
                        </p>

                        <div style="background: #1c2028; border: 1.5px solid #1e222b; padding: 1rem; border-radius: 10px; margin: 1.5rem 0; box-sizing: border-box;">
                            <span style="font-size: 0.85rem; color: #9ca3af; display: block; margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.5px;">
                                Hasil Asesmen
                            </span>
                            <div style="text-align: center; margin: 2rem 0;">
                                <a href="{file_url}" target="_blank" style="display: inline-block; height: 46px; line-height: 46px; background: #2f60f5; color: #ffffff; text-decoration: none; border-radius: 10px; font-size: 0.95rem; font-weight: 600; padding: 0 24px; box-sizing: border-box; transition: all 0.2s ease; box-shadow: 0 4px 12px rgba(47, 96, 245, 0.2);">
                                    📥 Unduh Hasil Asesmen (Excel)
                                </a>
                            </div>
                        </div>

                        <p style="color: #64748b; font-size: 0.85rem; line-height: 1.5; margin-bottom: 2rem; font-style: italic;">
                            Catatan: Mohon gunakan hasil ini sebagai referensi awal saja. Sangat disarankan untuk berkonsultasi dengan profesional (psikolog/psikiater) apabila Anda membutuhkan penanganan atau validasi medis lebih lanjut.
                        </p>

                        <hr style="border: none; border-top: 1px solid #1e222b; margin-bottom: 1.5rem;">
                        
                        <p style="margin: 0; text-align: center; font-size: 0.85rem; color: #9ca3af; line-height: 1.4;">
                            Salam hangat,<br>
                            <strong style="color: #ffffff; font-weight: 600; display: inline-block; margin-top: 4px;">
                                Chatbot Kesehatan Mental UGM
                            </strong>
                        </p>
                    </div>
                </body>
            </html>
            """
            
            msg['Subject'] = "Hasil Asesmen Chatbot Kesehatan Mental UGM"
            msg['From'] = settings.MAIL_DEFAULT_SENDER
            msg['To'] = recipient
            msg.attach(MIMEText(html_content, "html"))

            if file_content:
                part = MIMEBase("application", "vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                part.set_payload(file_content)

                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f'attachment; filename="{file_name}"'
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
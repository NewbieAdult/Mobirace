# Nguyễn Tuấn Minh
# 27/06/2023

from fastapi import File, UploadFile, HTTPException, status
from fastapi.templating import Jinja2Templates
from typing import Optional, List
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
# from lib.xlsx2html import xlsx2html
from email import encoders
import smtplib
import os
from email.message import EmailMessage

# Function tạo template HTML
def create_html_from_template(template_path: str, fillin_dict: dict):
    directory_path, filename = os.path.split(template_path)
    fillin_dict["request"] = None
    templates = Jinja2Templates(directory=directory_path)
    rendered_content = templates.TemplateResponse(filename, fillin_dict)
    html_content = rendered_content.body.decode()
    return html_content



# Function gửi mail theo template HTML có gắn kèm files
#son.buingoc edited and optimized on 13/07/2023
def send_email_with_html_template(email_sender: str, 
                                email_password: str, 
                                smtp_server: str, 
                                smtp_port: int, 
                                html_template_file_path: str,
                                html_fillin_dict: dict, 
                                receivers: List[str],
                                attach_files: List[UploadFile]=None,
                                subject: Optional[str]=None, 
                            ):
    receivers_email_string =  ', '.join(receivers)
    # Chuẩn bị email
    msg = MIMEMultipart()
    msg["From"] = email_sender
    msg["To"] = receivers_email_string
    msg["Subject"] = subject
        
    # Điền các tham số còn thiếu vào template
    try:
        msg.attach(MIMEText(create_html_from_template(html_template_file_path, html_fillin_dict), "html"))

        # Đính kèm files vào email
        for file in (attach_files or []):
            file_data = file.file.read()
            
            # Tạo đối tượng MIMEBase với các thông tin và dữ liệu từ tệp đính kèm
            attachment = MIMEBase("application", "octet-stream")
            attachment.set_payload(file_data)
            
            # Mã hóa dữ liệu tệp đính kèm thành base64
            encoders.encode_base64(attachment)
        
            # Thiết lập tiêu đề và tên tệp đính kèm
            attachment.add_header(
                "Content-Disposition",
                "attachment",
                filename=file.filename
            )
        
            # Thêm tệp đính kèm vào email
            msg.attach(attachment)

        # Kết nối SMTP server và gửi email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(email_sender, email_password)
            server.send_message(msg)
        
        return {"detail": "Thao tác thành công!"}
    except:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail = "Thao tác không thành công")
    



# Function gửi mail theo template plain có gắn kèm files
#son.buingoc edited and optimized on 13/07/2023
def send_email_without_html_template(email_sender: str, 
                                    email_password: str, 
                                    smtp_server: str, 
                                    smtp_port: int,
                                    body: str,
                                    receivers: List[str],
                                    attach_files: List[UploadFile]=None,
                                    is_html_message: bool=False,
                                    message: Optional[str]=None,
                                    subject: Optional[str]=None
                                    ):
    receivers_email_string =  ', '.join(receivers)
    # Chuẩn bị email
    # msg = MIMEMultipart()
    msg = EmailMessage()
    msg["From"] = email_sender
    msg["To"] = receivers_email_string
    msg["Subject"] = subject
    msg.set_content(body)
    try:   
        # if is_html_message == True:
        #     msg.attach(MIMEText(message, 'html'))
        # else:
        # msg.attach(MIMEText(message, 'plain'))
        # Đính kèm files vào email
        # Đính kèm files vào email
        # for file in (attach_files or []):
        #     file_data = file.file.read()
            
        #     # Tạo đối tượng MIMEBase với các thông tin và dữ liệu từ tệp đính kèm
        #     attachment = MIMEBase("application", "octet-stream")
        #     attachment.set_payload(file_data)
            
        #     # Mã hóa dữ liệu tệp đính kèm thành base64
        #     encoders.encode_base64(attachment)
        
        #     # Thiết lập tiêu đề và tên tệp đính kèm
        #     attachment.add_header(
        #         "Content-Disposition",
        #         "attachment",
        #         filename=file.filename
        #     )
        
        #     # Thêm tệp đính kèm vào email
        #     msg.attach(attachment)

    
        # Kết nối SMTP server và gửi email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(email_sender, email_password)
            server.send_message(msg)
        return {"detail": "Thao tác thành công"}
    except:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail = "Thao tác không thành công")
    

# Main function
#son.buingoc edited and optimized on 13/07/2023
def send_email(email_sender: str, 
               email_password: str, 
               smtp_server: str, 
               smtp_port: int,
               body: str,
               receivers: List[str],
               attach_files: List[UploadFile]=None,
               html_content_in_excel_files: List[UploadFile]=None,
               html_template_file_path: Optional[str] = None,
               html_fillin_dict: Optional[dict] = None,
               message: Optional[str] = None,
               is_html_message: Optional[bool] = False,
               subject: Optional[str]= None    
               ):
    
    # if is_html_message:
    #     for file in (html_content_in_excel_files or []):
    #         message += "</br>" + xlsx2html(file)
    
    if html_template_file_path is None:
        return send_email_without_html_template(email_sender=email_sender, 
                                                email_password=email_password, 
                                                smtp_server=smtp_server, 
                                                smtp_port=smtp_port, 
                                                body=body,
                                                receivers=receivers, 
                                                attach_files=attach_files, 
                                                is_html_message=is_html_message, 
                                                message=message,
                                                subject=subject)
    else:
        return send_email_with_html_template(email_sender=email_sender, 
                                             email_password=email_password, 
                                             smtp_server=smtp_server, 
                                             smtp_port=smtp_port, 
                                             html_template_file_path=html_template_file_path, 
                                             html_fillin_dict=html_fillin_dict, 
                                             receivers=receivers, 
                                             attach_files=attach_files, 
                                             subject=subject)
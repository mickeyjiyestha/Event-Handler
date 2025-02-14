import gspread
from oauth2client.service_account import ServiceAccountCredentials
import qrcode
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import os
from datetime import datetime, timedelta
import time

# Konfigurasi
SPREADSHEET_ID = '#'
SHEET_NAME = '#'
CREDS_FILE = '#'
EMAIL_USER = '#'
EMAIL_PASSWORD = '#'  # Ganti dengan App Password Anda

# Setup Google Sheets
scope = ['https://www.googleapis.com/auth/spreadsheets']
creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, scope)
client = gspread.authorize(creds)

# Akses spreadsheet dan worksheet
spreadsheet = client.open_by_key(SPREADSHEET_ID)
sheet = spreadsheet.worksheet(SHEET_NAME)

def generate_qr(email):
    data = f"{email}|{datetime.now().timestamp()}"
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    filename = f"qrcode_{email.split('@')[0]}.png"
    img.save(filename)
    return filename

def send_email(to_email, qr_file):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_USER
    msg['To'] = to_email
    msg['Subject'] = "QR Code Registrasi Event Anda"
    
    body = """
    <h2>Terima kasih telah mendaftar!</h2>
    <p>Berikut QR Code Anda untuk check-in di lokasi event:</p>
    <img src="cid:qrcode">
    <p>Harap simpan QR Code ini dan tunjukkan saat check-in.</p>
    """
    msg.attach(MIMEText(body, 'html'))
    
    with open(qr_file, 'rb') as f:
        img = MIMEImage(f.read())
        img.add_header('Content-ID', '<qrcode>')
        msg.attach(img)
    
    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.login(EMAIL_USER, EMAIL_PASSWORD)
    server.sendmail(EMAIL_USER, to_email, msg.as_string())
    server.quit()
    
    os.remove(qr_file)  # Hapus file setelah dikirim

def process_registrations():
    records = sheet.get_all_records()
    
    # Debugging: Cetak semua record
    print("All records:", records)
    
    # Hanya proses data yang lebih baru dari 1 jam yang lalu
    cutoff_time = datetime.now() - timedelta(hours=1)
    
    for idx, record in enumerate(records, start=2):
        # Parse timestamp dari record
        try:
            record_time = datetime.strptime(record['Timestamp'], '%m/%d/%Y %H:%M:%S')
        except ValueError:
            record_time = datetime.strptime(record['Timestamp'], '%Y-%m-%d %H:%M:%S')
        
        # Cek apakah data baru dan belum diproses
        if record_time > cutoff_time and not record.get('QR Terkirim'):
            try:
                email = record['Email Address']
                qr_file = generate_qr(email)
                send_email(email, qr_file)
                sheet.update_cell(idx, 6, 'Yes')  # Update kolom status menjadi "Yes"
                print(f"Success: {email}")
            except Exception as e:
                print(f"Error processing {record}: {str(e)}")

if __name__ == "__main__":
    while True:
        print("Checking for new registrations...")
        process_registrations()
        print("Waiting for 5 seconds before checking again...")
        time.sleep(5)  # Tunggu 5 detik sebelum memeriksa lagi
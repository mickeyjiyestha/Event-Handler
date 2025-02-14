# qr_attendance.py
from flask import Flask, request, jsonify
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from flask_cors import CORS  # Import library CORS

# Konfigurasi
SPREADSHEET_ID = '1KuLZ4Vek_K1kzYhBs-g0uXeRqcx02mt8BwqrmFoeAHg'
SHEET_NAME = 'Form Responses 1'
CREDS_FILE = 'credentials.json'

# Setup Google Sheets
scope = ['https://www.googleapis.com/auth/spreadsheets']
creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, scope)
client = gspread.authorize(creds)
spreadsheet = client.open_by_key(SPREADSHEET_ID)
sheet = spreadsheet.worksheet(SHEET_NAME)

app = Flask(__name__)
CORS(app)  # Aktifkan CORS untuk semua route

@app.route('/scan_qr', methods=['POST'])
def scan_qr():
    # Ambil data dari QR Code
    data = request.json.get('data')
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    # Pisahkan email dan timestamp dari data QR Code
    try:
        email, timestamp = data.split('|')
    except ValueError:
        return jsonify({'error': 'Invalid QR Code format'}), 400

    # Cari record di spreadsheet berdasarkan email
    records = sheet.get_all_records()
    for idx, record in enumerate(records, start=2):
        record_email = record['Email Address']
        if record_email == email:
            # Update kolom "Attendance" menjadi True
            sheet.update_cell(idx, 7, 'True')  # Kolom ke-7 adalah "Attendance"
            return jsonify({'message': f'Attendance updated for {email}'}), 200

    # Jika email tidak ditemukan
    return jsonify({'error': 'Email not found in the spreadsheet'}), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
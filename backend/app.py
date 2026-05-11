from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from imap_tools import MailBox, AND
from datetime import date
import io
import zipfile
import traceback

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return jsonify({
        'status': 'online', 
        'message': 'Gmail Attachment Downloader API is running! Use the /download endpoint to fetch attachments.'
    })

@app.route('/download', methods=['POST'])
def download_attachments():
    try:
        data = request.json

        email = data.get('email')
        password = data.get('password')
        start_str = data.get('start_date')
        end_str = data.get('end_date')
        extension_filter = data.get('extension', '').strip().lower()

        if not all([email, password, start_str, end_str]):
            return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400

        start = start_str.split('-')
        end = end_str.split('-')

        start_date = date(int(start[0]), int(start[1]), int(start[2]))
        end_date = date(int(end[0]), int(end[1]), int(end[2]))

        memory_file = io.BytesIO()
        
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            mailbox = MailBox('imap.gmail.com').login(email, password)
            try:
                messages = mailbox.fetch(
                    AND(date_gte=start_date, date_lt=end_date),
                    reverse=True
                )

                for msg in messages:
                    mail_date = msg.date.strftime('%Y-%m-%d')
                    
                    for att in msg.attachments:
                        filename = att.filename
                        if not filename:
                            continue
                            
                        # Filter by extension if provided
                        if extension_filter:
                            if not extension_filter.startswith('.'):
                                extension_filter = '.' + extension_filter
                            if not filename.lower().endswith(extension_filter):
                                continue

                        # Use a safe path inside the zip file
                        zip_path = f"{mail_date}/{filename}"
                        zf.writestr(zip_path, att.payload)
            except Exception as fetch_err:
                print("Warning during fetch:", fetch_err)
            finally:
                try:
                    mailbox.logout()
                except Exception as logout_err:
                    print("Ignored logout error:", logout_err)

        memory_file.seek(0)
        
        # Check if zip is empty
        try:
            with zipfile.ZipFile(memory_file, 'r') as z:
                if not z.namelist():
                    return jsonify({'status': 'error', 'message': 'No attachments found matching the criteria'}), 404
        except zipfile.BadZipFile:
            return jsonify({'status': 'error', 'message': 'Failed to create zip file'}), 500
            
        memory_file.seek(0)

        return send_file(
            memory_file,
            mimetype='application/zip',
            as_attachment=True,
            download_name='attachments.zip'
        )

    except Exception as e:
        print("Error:", traceback.format_exc())
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

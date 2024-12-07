from flask import Flask, render_template, request, redirect, url_for, send_file
import pandas as pd
from fpdf import FPDF
import firebase_admin
from firebase_admin import credentials, firestore
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

app = Flask(__name__)

# Initialize Firebase
cred = credentials.Certificate('firebase.json')  # Update with your path
firebase_admin.initialize_app(cred)
db = firestore.client()

def send_email(to_email, subject, body):
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    from_email = "mail.linxora@gmail.com" 
    to_email="unknowngumnam52@gmail.com"
    password = "hgrm hzcd vhlw dtow"  

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(from_email, password)
        server.send_message(msg)
        print("Email sent successfully!")

    except Exception as e:
        print(f"Failed to send email: {e}")

    finally:
        server.quit()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/contact-form')
def contact_form():
    return render_template('contact_form.html')

@app.route('/add-client', methods=['POST'])
def add_client():
    name = request.form['name']
    contact_number = request.form['contact_number']
    email = request.form['email']
    quotation = request.form['quotation']
    service = request.form['service']
    message = request.form['message']

    # Save client to Firebase
    db.collection('clients').add({
        'name': name,
        'contact_number': contact_number,
        'email': email,
        'quotation': quotation,
        'service': service,
        'message': message
    })

    # Send email
    subject = f"Message from {name}"
    send_email(email, subject, message)

    return redirect(url_for('thank_you'))

@app.route('/display-data')
def display_data():
    clients_ref = db.collection('clients')
    clients = clients_ref.stream()

    client_data = []
    for client in clients:
        client_dict = client.to_dict()
        client_dict['id'] = client.id
        client_data.append(client_dict)

    return render_template('display_data.html', clients=client_data)

@app.route('/delete-client/<client_id>', methods=['POST'])
def delete_client(client_id):
    db.collection('clients').document(client_id).delete()
    return redirect(url_for('display_data'))

@app.route('/delete-all', methods=['POST'])
def delete_all():
    clients_ref = db.collection('clients')
    clients = clients_ref.stream()

    for client in clients:
        clients_ref.document(client.id).delete()

    return redirect(url_for('display_data'))

@app.route('/export-csv')
def export_csv():
    clients_ref = db.collection('clients')
    clients = clients_ref.stream()

    client_data = [client.to_dict() for client in clients]
    df = pd.DataFrame(client_data)
    csv_file = 'clients.csv'
    df.to_csv(csv_file, index=False)

    return send_file(csv_file, as_attachment=True)

@app.route('/export-pdf')
def export_pdf():
    clients_ref = db.collection('clients')
    clients = clients_ref.stream()

    client_data = [client.to_dict() for client in clients]

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Create table header
    pdf.cell(40, 10, 'Name', 1)
    pdf.cell(40, 10, 'Contact Number', 1)
    pdf.cell(60, 10, 'Email', 1)
    pdf.cell(30, 10, 'Quotation', 1)
    pdf.cell(30, 10, 'Service', 1)
    pdf.cell(30, 10, 'Message', 1)
    pdf.ln()

    # Add data to the table
    for client in client_data:
        pdf.cell(40, 10, str(client.get('name', '')), 1)
        pdf.cell(40, 10, str(client.get('contact_number', '')), 1)
        pdf.cell(60, 10, str(client.get('email', '')), 1)
        pdf.cell(30, 10, str(client.get('quotation', '')), 1)
        pdf.cell(30, 10, str(client.get('service', '')), 1)
        pdf.cell(30, 10, str(client.get('message', '')), 1)
        pdf.ln()

    pdf_file = 'clients.pdf'
    pdf.output(pdf_file)

    return send_file(pdf_file, as_attachment=True)

@app.route('/upload-excel', methods=['GET', 'POST'])
def upload_excel():
    if request.method == 'POST':
        file = request.files['file']
        if file and file.filename.endswith('.xlsx'):
            df = pd.read_excel(file)

            # Check if required columns exist
            required_columns = ['name', 'contact_number', 'email', 'quotation', 'service', 'message']
            if not all(col in df.columns for col in required_columns):
                return "Error: Excel file must contain the following columns: " + ", ".join(required_columns), 400
            
            for _, row in df.iterrows():
                db.collection('clients').add({
                    'name': row['name'],
                    'contact_number': row['contact_number'],
                    'email': row['email'],
                    'quotation': row['quotation'],
                    'service': row['service'],
                    'message': row['message']
                })
            return redirect(url_for('display_data'))

    return render_template('upload_excel.html')

@app.route('/thank-you')
def thank_you():
    return render_template('thank_you.html')

if __name__ == '__main__':
    app.run(debug=True)

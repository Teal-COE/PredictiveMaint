# Importing necessary libraries for email composition and SMTP server interaction
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email_to_multiple_recipients(subject, body, email_details):
    """
    Sends an email to multiple recipients with optional CC and BCC.

    Args:
        subject (str): The subject of the email.
        body (str): The body of the email (in HTML format).
        email_details (dict): A dictionary containing:
            - 'to' (list or str): List or comma-separated string of recipient emails.
            - 'cc' (list or str): List or comma-separated string of CC emails (optional).
            - 'bcc' (list or str): List or comma-separated string of BCC emails (optional).
            - 'sender' (str): The sender's email address.
    """
    # SMTP server configuration for sending emails using Outlook
    smtp_server = 'smtp.office365.com'
    smtp_port = 587
    sender_email = email_details.get('sender', 'tealappmailer1@titan.co.in')

    # WARNING: Replace hard-coded password with a secure credential storage method
    sender_password = 'Teal@2025'

    # Extract and parse email recipients from input
    to_email = email_details.get('to', [])
    cc_email = email_details.get('cc', [])
    bcc_email = email_details.get('bcc', [])

    # Convert string inputs to lists for consistency
    if isinstance(to_email, str):
        to_email = to_email.split(",")
    if isinstance(cc_email, str):
        cc_email = cc_email.split(",")
    if isinstance(bcc_email, str):
        bcc_email = bcc_email.split(",")

    try:
        # Create an email object with subject, sender, and recipients
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = sender_email
        msg["To"] = ", ".join(to_email)
        msg["Cc"] = ", ".join(cc_email)
        msg["In-Reply-To"] = "tealappmailer1@titan.co.in"

        # Attach the email body as HTML
        html_body = MIMEText(body, "html")
        msg.attach(html_body)

        # Combine all recipients (To, CC, BCC) for the SMTP server
        all_recipients = to_email + cc_email + bcc_email

        # Connect to the SMTP server and send the email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Secure the connection using TLS
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, all_recipients, msg.as_string())
            print("Email sent successfully.")

    except Exception as e:
        print(f"Failed to send email: {e}")

def send_sensor_alerts(sensor_data, email_details):
    """
    Prepares and sends an alert email with sensor data in a tabular format.

    Args:
        sensor_data (dict): Dictionary containing sensor details.
        email_details (dict): Email configuration details.
    """
    # Subject of the alert email
    subject = "Predictive Analysis Alerts"

    # Generate an HTML table dynamically from the sensor data
    table_rows = ""
    for sensor_id, details in sensor_data.items():
        table_rows += f"""
        <tr>
            <td>{details['sensor_name']}</td>
            <td>{details['might_fail_at']}</td>
            <td>{details['failure']}</td>
            <td>{details['score']}</td>
        </tr>
        """

    # Full HTML body for the email, including styling
    body = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
                color: #333;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }}
            th, td {{
                border: 1px solid #ddd;
                text-align: center;
                padding: 12px;
            }}
            th {{
                background-color: #0056b3;
                color: #fff;
            }}
            tr:nth-child(even) {{
                background-color: #f9f9f9;
            }}
            tr:hover {{
                background-color: #f1f1f1;
            }}
        </style>
    </head>
    <body>
        <h2>Predictive Analysis Alerts</h2>
        <table>
            <tr>
                <th>Sensor Name</th>
                <th>Might Fail At</th>
                <th>Failure</th>
                <th>Score</th>
            </tr>
            {table_rows}
        </table>
    </body>
    </html>
    """
    # Send the email using the helper function
    send_email_to_multiple_recipients(subject, body, email_details)

# Example sensor data for the alert email
sensor_data = {
    "S1": {"sensor_name": "Temperature Sensor", "might_fail_at": "2024-11-26 07:00", "failure": "27°C", "score": 40},
    "S2": {"sensor_name": "Pressure Sensor", "might_fail_at": "2024-11-27 08:30", "failure": "40°C", "score": 23},
    "S3": {"sensor_name": "Temperature 1", "might_fail_at": "2024-11-25 07:00", "failure": "21°C", "score": 12},
    "S4": {"sensor_name": "Pressure 2", "might_fail_at": "2024-11-20 08:30", "failure": "45°C", "score": 10},
}

# Email configuration with recipients and sender details
email_details = {
    "to": ["akashadi@titan.co.in", "venkataprasad@titan.co.in"],
    "cc": ["sanjaybaswa@titan.co.in"],
    "bcc": ["faj@titan.co.in"],
    "sender": "tealappmailer1@titan.co.in",
}

# Send sensor alerts
send_sensor_alerts(sensor_data, email_details)


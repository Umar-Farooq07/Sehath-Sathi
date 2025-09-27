# Install dependencies if not already:
# pip install twilio flask sqlite3

from twilio.rest import Client
from flask import Flask, request, Response
from twilio.twiml.voice_response import VoiceResponse, Gather
import sqlite3
import datetime
import threading
import time


import sqlite3
from datetime import datetime, timedelta

# conn = sqlite3.connect('medicine_reminder.db')
# cursor = conn.cursor()

# # Get local time (your timezone)
# now_local = datetime.now()  # Local time
# time_for_call = now_local + timedelta(minutes=1)  # 5 minutes from now

# cursor.execute("""
#     INSERT INTO schedules (patient_name, caretaker_name, patient_number, caretaker_number, tablet_name, time)
#     VALUES (?, ?, ?, ?, ?, ?)
# """, ('Umar', 'Farooq', '+916362511760', '+916362511760', 'Tusq', time_for_call))

# conn.commit()
# conn.close()






# ------------------ CONFIG ------------------
TWILIO_ACCOUNT_SID = "AC66b8b0b6a46a3a378a54e4c79e3c43d2"
TWILIO_AUTH_TOKEN = "c6a33941c7b1ecb0f5121b621140bc9d"
TWILIO_NUMBER = "+12707431760"       # Twilio number

DATABASE = "medicine_reminder.db"
NGROK_URL = "https://ada-rampageous-taillessly.ngrok-free.dev"

twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# ------------------ FLASK APP ------------------
app = Flask(__name__)

# ------------------ TWILIO VOICE ENDPOINT ------------------
@app.route("/voice", methods=['GET', 'POST'])
def voice():
    """Twilio calls this endpoint to get instructions."""
    schedule_id = request.args.get('schedule_id')
    tablet_name = request.args.get('tablet_name', 'your tablet')

    resp = VoiceResponse()

    gather = Gather(
        input='speech dtmf',
        num_digits=1,
        timeout=5,
        action='/gather?schedule_id={}'.format(schedule_id)
    )
    gather.say(
        f"Hello! Did you take your {tablet_name} today? Please say yes or no, or press 1 for yes, 2 for no.",
        voice='alice'
    )
    resp.append(gather)
    resp.say("We did not receive your response. Goodbye!")
    return Response(str(resp), mimetype='text/xml')


# ------------------ GATHER RESPONSE ------------------
@app.route("/gather", methods=['GET', 'POST'])
def gather():
    schedule_id = request.args.get('schedule_id')
    resp = VoiceResponse()
    speech_result = request.values.get('SpeechResult', '').lower()
    dtmf = request.values.get('Digits', '')

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT patient_name, caretaker_name, patient_number, caretaker_number, tablet_name, missed_attempts FROM schedules WHERE id=?",
        (schedule_id,)
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        resp.say("Schedule not found. Goodbye!", voice='alice')
        resp.hangup()
        return Response(str(resp), mimetype='text/xml')

    patient_name, caretaker_name, patient_number, caretaker_number, tablet_name, missed_attempts = row

    print("Speech result:", speech_result)
    print("DTMF input:", dtmf)

    # Responses
    if 'yes' in speech_result or dtmf == '1':
        resp.say(f"Great! Thank you for taking your {tablet_name}.", voice='alice')
    elif 'no' in speech_result or dtmf == '2':
        resp.say(f"Please take your {tablet_name} now. We will call you again in 5 minutes to reconfirm.", voice='alice')
        threading.Timer(5*60, lambda: make_call(schedule_id)).start()
    else:
        resp.say(f"Could not understand your response. Asking again.", voice='alice')
        threading.Timer(10, lambda: make_call(schedule_id)).start()

    resp.hangup()
    return Response(str(resp), mimetype='text/xml')


# ------------------ CALL STATUS CALLBACK ------------------
@app.route("/status", methods=['POST'])
def call_status():
    call_status = request.values.get('CallStatus', '')
    schedule_id = request.args.get('schedule_id')
    print("Call ended with status:", call_status)

    if call_status in ['no-answer', 'failed', 'busy']:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("UPDATE schedules SET missed_attempts = missed_attempts + 1 WHERE id=?", (schedule_id,))
        cursor.execute("SELECT missed_attempts, caretaker_number FROM schedules WHERE id=?", (schedule_id,))
        row = cursor.fetchone()
        conn.commit()
        conn.close()

        missed_attempts, caretaker_number = row
        if missed_attempts >= 3:
            send_alert_to_caretaker(caretaker_number)

    return ('', 204)


# ------------------ SEND ALERT ------------------
def send_alert_to_caretaker(caretaker_number):
    message = twilio_client.messages.create(
        body="⚠️ Patient did not respond to the medicine reminder after 3 calls!",
        from_=TWILIO_NUMBER,
        to=caretaker_number
    )
    print("Alert SMS sent. SID:", message.sid)


# ------------------ MAKE CALL ------------------
def make_call(schedule_id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT patient_number, tablet_name FROM schedules WHERE id=?", (schedule_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        print(f"No schedule found for ID {schedule_id}")
        return
    patient_number, tablet_name = row

    call = twilio_client.calls.create(
        url=f"{NGROK_URL}/voice?schedule_id={schedule_id}&tablet_name={tablet_name}",
        from_=TWILIO_NUMBER,
        to=patient_number,
        status_callback=f"{NGROK_URL}/status?schedule_id={schedule_id}",
        status_callback_event=['completed', 'no-answer', 'busy', 'failed']
    )
    print("Call initiated. SID:", call.sid)


# ------------------ SCHEDULER THREAD ------------------
def schedule_checker():
    while True:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("SELECT id FROM schedules WHERE time <= ? AND status = 0", (now_str,))
        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            schedule_id = row[0]
            print(f"Triggering call for schedule ID: {schedule_id}")
            make_call(schedule_id)
            # mark as called to prevent repeated calls
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute("UPDATE schedules SET status = 1 WHERE id=?", (schedule_id,))
            conn.commit()
            conn.close()

        time.sleep(10)  # check every 10 seconds



# ------------------ RUN ------------------
if __name__ == "__main__":
    threading.Thread(target=schedule_checker, daemon=True).start()
    print("Starting Flask server on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000)

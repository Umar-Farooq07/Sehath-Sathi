# Install dependencies if not already:
# pip install twilio flask pymongo

from twilio.rest import Client
from flask import Flask, request, Response
from twilio.twiml.voice_response import VoiceResponse, Gather
from pymongo import MongoClient
from datetime import datetime, timedelta
import threading
import time

from pymongo import MongoClient
from datetime import datetime, timedelta
import uuid

# ------------------ MONGO DB SETUP ------------------
mongo_client = MongoClient("mongodb://localhost:27017")
db = mongo_client.medicine_reminder
schedules_collection = db.schedules

# ------------------ INSERT TEST SCHEDULE ------------------
# Generate a unique ID for the schedule
schedule_id = str(uuid.uuid4())

# Schedule a call 1 minute from now
time_for_call = datetime.now() + timedelta(minutes=1)

test_schedule = {
    "_id": schedule_id,
    "patient_name": "Umar",
    "caretaker_name": "Farooq",
    "patient_number": "+916362511760",
    "caretaker_number": "+916362511760",
    "tablet_name": "Tusq",
    "time": time_for_call,
    "status": 0,            # 0 = not called yet
    "missed_attempts": 0
}

schedules_collection.insert_one(test_schedule)

print(f"Inserted test schedule with ID: {schedule_id}")
print(f"Scheduled time: {time_for_call}")


# ------------------ CONFIG ------------------
TWILIO_ACCOUNT_SID = "AC66b8b0b6a46a3a378a54e4c79e3c43d2"
TWILIO_AUTH_TOKEN = "c6a33941c7b1ecb0f5121b621140bc9d"
TWILIO_NUMBER = "+12707431760"       # Twilio number
NGROK_URL = "https://ada-rampageous-taillessly.ngrok-free.dev"

twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# ------------------ MONGODB SETUP ------------------
mongo_client = MongoClient("mongodb://localhost:27017")
db = mongo_client.medicine_reminder
schedules_collection = db.schedules

# ------------------ FLASK APP ------------------
app = Flask(__name__)

# ------------------ TWILIO VOICE ENDPOINT ------------------
@app.route("/voice", methods=['GET', 'POST'])
def voice():
    schedule_id = request.args.get('schedule_id')
    tablet_name = request.args.get('tablet_name', 'your tablet')

    resp = VoiceResponse()
    gather = Gather(
        input='speech dtmf',
        num_digits=1,
        timeout=5,
        action=f'/gather?schedule_id={schedule_id}'
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

    schedule = schedules_collection.find_one({"_id": schedule_id})
    if not schedule:
        resp.say("Schedule not found. Goodbye!", voice='alice')
        resp.hangup()
        return Response(str(resp), mimetype='text/xml')

    patient_number = schedule['patient_number']
    tablet_name = schedule['tablet_name']
    caretaker_number = schedule['caretaker_number']
    missed_attempts = schedule.get('missed_attempts', 0)

    print("Speech result:", speech_result)
    print("DTMF input:", dtmf)

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

    schedule = schedules_collection.find_one({"_id": schedule_id})
    if not schedule:
        return ('', 204)

    # Initialize busy_attempts if not present
    busy_attempts = schedule.get('busy_attempts', 0)

    if call_status == 'busy':
        busy_attempts += 1
        schedules_collection.update_one(
            {"_id": schedule_id},
            {"$set": {"busy_attempts": busy_attempts}}
        )
        print(f"Busy attempt #{busy_attempts} for schedule {schedule_id}")

        if busy_attempts < 3:
            print("Retrying call in 1 minute...")
            threading.Timer(60, lambda: make_call(schedule_id)).start()
        else:
            print("3 busy attempts reached. Sending alert to caretaker.")
            send_alert_to_caretaker(schedule['caretaker_number'])

    elif call_status in ['no-answer', 'failed']:
        missed_attempts = schedule.get('missed_attempts', 0) + 1
        schedules_collection.update_one({"_id": schedule_id}, {"$set": {"missed_attempts": missed_attempts}})
        print(f"Missed attempt #{missed_attempts} for schedule {schedule_id}")

        if missed_attempts >= 3:
            send_alert_to_caretaker(schedule['caretaker_number'])

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
    schedule = schedules_collection.find_one({"_id": schedule_id})
    if not schedule:
        print(f"No schedule found for ID {schedule_id}")
        return

    patient_number = schedule['patient_number']
    tablet_name = schedule['tablet_name']

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
        now = datetime.now()
        pending_schedules = schedules_collection.find({
            "time": {"$lte": now},
            "status": 0
        })
        for schedule in pending_schedules:
            schedule_id = schedule['_id']
            print(f"Triggering call for schedule ID: {schedule_id}")
            make_call(schedule_id)
            schedules_collection.update_one({"_id": schedule_id}, {"$set": {"status": 1}})
        time.sleep(10)

# ------------------ RUN ------------------
if __name__ == "__main__":
    threading.Thread(target=schedule_checker, daemon=True).start()
    print("Starting Flask server on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000)

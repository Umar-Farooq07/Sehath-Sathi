# Install dependencies if not already:
# pip install twilio flask

from twilio.rest import Client
from flask import Flask, request, Response
from twilio.twiml.voice_response import VoiceResponse, Gather

# ------------------ CONFIG ------------------
TWILIO_ACCOUNT_SID = "AC66b8b0b6a46a3a378a54e4c79e3c43d2"
TWILIO_AUTH_TOKEN = "2dafcebb40f1cddb44c9388ecb457ec0"
TWILIO_NUMBER = "+12707431760"       # Twilio number
PATIENT_NUMBER = "+916362511760"     # Patient number
CARETAKER_NUMBER = "+916362511760"   # Caretaker number

twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# ------------------ FLASK APP ------------------
app = Flask(__name__)

# ------------------ TWILIO VOICE ENDPOINT ------------------
@app.route("/voice", methods=['GET', 'POST'])
def voice():
    """Twilio calls this endpoint to get instructions."""
    resp = VoiceResponse()

    # Gather patient response (speech or DTMF)
    gather = Gather(input='speech dtmf', num_digits=1, timeout=5, action='/gather')
    gather.say(
        "Hello! Did you take your tablets today? Please say yes or no, or press 1 for yes, 2 for no.",
        voice='alice'
    )
    resp.append(gather)

    resp.say("We did not receive your response. Goodbye!")
    return Response(str(resp), mimetype='text/xml')


@app.route("/gather", methods=['GET', 'POST'])
def gather():
    """Handle patient response."""
    resp = VoiceResponse()
    speech_result = request.values.get('SpeechResult', '').lower()
    dtmf = request.values.get('Digits', '')

    print("Speech result:", speech_result)
    print("DTMF input:", dtmf)

    if 'yes' in speech_result or dtmf == '1':
        resp.say("Great! Thank you for taking your tablets.", voice='alice')
    elif 'no' in speech_result or dtmf == '2':
        resp.say("Please take your tablets now. Alerting your caretaker.", voice='alice')
        send_alert_to_caretaker()
    else:
        resp.say("Could not understand your response. Alerting your caretaker.", voice='alice')
        send_alert_to_caretaker()

    resp.hangup()
    return Response(str(resp), mimetype='text/xml')


# ------------------ CALL STATUS CALLBACK ------------------
@app.route("/status", methods=['POST'])
def call_status():
    """Triggered when a call ends."""
    call_status = request.values.get('CallStatus', '')
    print("Call ended with status:", call_status)

    # If patient didn't pick up or call failed, alert caretaker immediately
    if call_status in ['no-answer', 'failed', 'busy']:
        send_alert_to_caretaker()

    return ('', 204)  # empty response


# ------------------ SEND ALERT ------------------
def send_alert_to_caretaker():
    message = twilio_client.messages.create(
        body="⚠️ Patient did not respond to the medicine reminder!",
        from_=TWILIO_NUMBER,
        to=CARETAKER_NUMBER
    )
    print("Alert SMS sent. SID:", message.sid)


# ------------------ MAKE CALL ------------------
def make_call():
    """Initiate a call to the patient via Twilio."""
    call = twilio_client.calls.create(
        url='https://ada-rampageous-taillessly.ngrok-free.dev/voice',  # Replace with your active ngrok URL
        from_=TWILIO_NUMBER,
        to=PATIENT_NUMBER,
        status_callback='https://ada-rampageous-taillessly.ngrok-free.dev/status',
        status_callback_event=['completed', 'no-answer', 'busy', 'failed']
    )
    print("Call initiated. SID:", call.sid)


# ------------------ RUN ------------------
if __name__ == "__main__":
    print("Starting Flask server on http://localhost:5000")
    print("Use ngrok to create a public HTTPS URL and replace the URL in make_call()")
    # Start first call after Flask is running
    make_call()
    app.run(host='0.0.0.0', port=5000)

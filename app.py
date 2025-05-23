from flask import Flask, request, Response
from twilio.twiml.voice_response import VoiceResponse, Gather
from google.cloud import dialogflow_v2 as dialogflow
import os

# Configuración
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/etc/secrets/whatsappagent-qcxq-393346593d28.json"
PROJECT_ID = "whatsappagent-qcxq"
LANGUAGE_CODE = "es"
SESSION_ID = "123456"  # puede ser el número del cliente

app = Flask(__name__)

@app.route("/voice", methods=["POST"])
def voice():
    voice = request.args.get("voice", "Google.es-US-Chirp3-HD-Leda")
    """Primer endpoint que Twilio llama al iniciar la llamada"""
    session_client = dialogflow.SessionsClient()
    session = session_client.session_path(PROJECT_ID, SESSION_ID)
    text_input = dialogflow.TextInput(text="Hola", language_code=LANGUAGE_CODE)
    query_input = dialogflow.QueryInput(text=text_input)
    
    response = session_client.detect_intent(request={"session": session, "query_input": query_input})
    bot_reply = response.query_result.fulfillment_text
    resp = VoiceResponse()
    gather = Gather(input="speech", action=f"/dialogflow?voice={voice}", method="POST", timeout=1,language="es-MX")
    gather.say(bot_reply, voice=voice)
    resp.append(gather)
    resp.redirect('/voice')  # Si no hubo respuesta, repite
    return Response(str(resp), mimetype="application/xml")

@app.route("/dialogflow", methods=["POST"])
def dialogflow_webhook():
    """Procesa la respuesta del cliente y consulta Dialogflow"""
    voice = request.args.get("voice", "Google.es-US-Chirp3-HD-Leda")
    user_text = request.form.get('SpeechResult')
    
    if not user_text:
        resp = VoiceResponse()
        resp.say("No te entendí. Intenta de nuevo.")
        resp.redirect('/voice')
        return Response(str(resp), mimetype="application/xml")

    # Enviar a Dialogflow
    session_client = dialogflow.SessionsClient()
    session = session_client.session_path(PROJECT_ID, SESSION_ID)
    text_input = dialogflow.TextInput(text=user_text, language_code=LANGUAGE_CODE)
    query_input = dialogflow.QueryInput(text=text_input)
    print(f"User input: {user_text}")
    response = session_client.detect_intent(request={"session": session, "query_input": query_input})
    bot_reply = response.query_result.fulfillment_text

    # Responder al usuario
    twiml = VoiceResponse()
    gather = Gather(input="speech", action="/dialogflow", method="POST", timeout=1,language="es-MX")
    gather.say(bot_reply, voice=voice)
    twiml.append(gather)
    twiml.redirect('/voice')  # Si no responde
    return Response(str(twiml), mimetype="application/xml")

if __name__ == "__main__":
    app.run(port=5000, debug=True)

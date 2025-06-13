from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import os
from langdetect import detect
from openai import OpenAI
import requests

app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

user_profiles = {}

def get_weather(city):
    api_key = os.getenv("OPENWEATHER_API_KEY")
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=fr"
    try:
        response = requests.get(url)
        data = response.json()
        if data.get("cod") != 200:
            return f"Je n'ai pas pu trouver la météo pour {city}."
        weather = data["weather"][0]["description"]
        temp = data["main"]["temp"]
        return f"La météo à {city} est actuellement : {weather}, avec une température de {temp}°C."
    except Exception:
        return "Une erreur est survenue en récupérant la météo."

def detect_intent(text):
    lowered = text.lower()
    if lowered in ["menu", "aide", "help"]:
        return "menu"
    if "je suis" in lowered and any(p in lowered for p in ["en couple", "solo", "avec enfants", "senior", "aventure", "romantique"]):
        return "profile_set"
    if any(x in lowered for x in ["bagage perdu", "bagage", "perdu", "lost luggage", "lost bag"]):
        return "baggage"
    if any(greet in lowered for greet in ["bonjour", "salut", "hello", "hi", "hey"]):
        return "greeting"
    if "météo" in lowered or "weather" in lowered:
        return "weather"
    if "restaurant" in lowered or "hôtel" in lowered or "hotel" in lowered:
        return "recommendation"
    if any(keyword in lowered for keyword in ["visiter", "tourisme", "à voir", "à faire", "guide", "lieux à", "monuments", "touristique"]):
        return "tourism"
    if any(keyword in lowered for keyword in ["programme", "circuit", "itinéraire", "planning", "jour par jour", "planning de visite"]):
        return "itinerary"
    return "chat"

def get_intro_by_lang(lang):
    if lang.startswith("fr"):
        return "👋 Bonjour ! Je suis Askély, votre assistant intelligent multilingue. Je peux vous aider à organiser votre voyage, découvrir les lieux à visiter, connaître la météo ou trouver les meilleures adresses locales."
    elif lang.startswith("en"):
        return "👋 Hello! I’m Askély, your smart multilingual assistant. I can help you discover tourist sites, check the weather, or find top local recommendations for your trip."
    else:
        return "👋 Hello! I’m Askély, your assistant. I can help with tourism, weather, recommendations and more!"

def get_menu(lang):
    if lang.startswith("fr"):
        return (
            "📋 *Menu Askély :*\n"
            "1️⃣ Météo → Ex: météo Paris\n"
            "2️⃣ Restaurants & hôtels → Ex: recommande un restaurant à Rome\n"
            "3️⃣ Circuits → Ex: programme de 3 jours à Dubaï\n"
            "4️⃣ Profil → Ex: je suis en couple\n"
            "5️⃣ Lieux à visiter → Ex: que visiter à Marrakech\n"
            "6️⃣ Bagages perdus → Ex: j'ai perdu mon bagage\n\n"
            "👉 Tape ton choix ou pose ta question librement."
        )
    else:
        return (
            "📋 *Askély Menu:*\n"
            "1️⃣ Weather → e.g. weather in Paris\n"
            "2️⃣ Restaurants & Hotels → e.g. recommend hotel in Madrid\n"
            "3️⃣ Travel Itinerary → e.g. 3-day plan for Tokyo\n"
            "4️⃣ Profile → e.g. I am solo traveler\n"
            "5️⃣ Tourist Guide → e.g. what to visit in Lisbon\n"
            "6️⃣ Lost Luggage → e.g. I lost my bag\n\n"
            "👉 Type your choice or ask freely."
        )
    if lang.startswith("fr"):
        return (
            "📋 *Menu Askély :*
"
            "1️⃣ Météo → Ex: météo Paris
"
            "2️⃣ Restaurants & hôtels → Ex: recommande un restaurant à Rome
"
            "3️⃣ Circuits → Ex: programme de 3 jours à Dubaï
"
            "4️⃣ Profil → Ex: je suis en couple
"
            "5️⃣ Lieux à visiter → Ex: que visiter à Marrakech
"
            "6️⃣ Bagages perdus → Ex: j'ai perdu mon bagage

"
            "👉 Tape ton choix ou pose ta question librement."
        )
    else:
        return (
            "📋 *Askély Menu:*
"
            "1️⃣ Weather → e.g. weather in Paris
"
            "2️⃣ Restaurants & Hotels → e.g. recommend hotel in Madrid
"
            "3️⃣ Travel Itinerary → e.g. 3-day plan for Tokyo
"
            "4️⃣ Profile → e.g. I am solo traveler
"
            "5️⃣ Tourist Guide → e.g. what to visit in Lisbon
"
            "6️⃣ Lost Luggage → e.g. I lost my bag

"
            "👉 Type your choice or ask freely."
        )

@app.route("/webhook/whatsapp", methods=["POST"])
def whatsapp_reply():
    incoming_msg = request.values.get('Body', '').strip()
    sender = request.values.get('From', '')
    lang = detect(incoming_msg)
    intent = detect_intent(incoming_msg)

    if intent == "menu":
        answer = get_menu(lang)

    elif intent == "profile_set":
        user_profiles[sender] = incoming_msg
        answer = "✅ Ton profil a bien été enregistré. Je personnaliserai désormais mes réponses selon tes préférences de voyage."

    elif intent == "greeting":
        answer = get_intro_by_lang(lang)

    elif intent == "weather":
        city = incoming_msg.split()[-1]
        answer = get_weather(city)

    elif intent == "recommendation":
        messages = [
            {"role": "system", "content": "Tu es Askély, un assistant intelligent qui recommande des restaurants, hôtels ou hébergements selon la ville et le besoin exprimé."},
            {"role": "user", "content": incoming_msg}
        ]
        response = client.chat.completions.create(model="gpt-4-turbo", messages=messages)
        answer = response.choices[0].message.content

    elif intent == "tourism":
        messages = [
            {"role": "system", "content": "Tu es Askély, un guide touristique virtuel expert du Maroc et du monde. Quand un utilisateur demande des conseils touristiques, propose-lui des idées de visites, d’activités culturelles, de monuments, de balades typiques et de spécialités locales."},
            {"role": "user", "content": incoming_msg}
        ]
        response = client.chat.completions.create(model="gpt-4-turbo", messages=messages)
        answer = response.choices[0].message.content

    elif intent == "itinerary":
        profil = user_profiles.get(sender, None)
        system_msg = "Tu es Askély, un expert en circuits touristiques internationaux. Propose des programmes jour par jour adaptés à la destination demandée, à la durée et au profil du voyageur si disponible."
        if profil:
            system_msg += f" Voici le profil de l'utilisateur : {profil}"
        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": incoming_msg}
        ]
        response = client.chat.completions.create(model="gpt-4-turbo", messages=messages)
        answer = response.choices[0].message.content

    elif intent == "baggage":
        messages = [
            {"role": "system", "content": "Tu es Askély, un assistant de voyage expert. Aide les utilisateurs à rédiger une réclamation ou à trouver les bonnes démarches en cas de bagage perdu à l'aéroport ou durant un vol."},
            {"role": "user", "content": incoming_msg}
        ]
        response = client.chat.completions.create(model="gpt-4-turbo", messages=messages)
        answer = response.choices[0].message.content

    else:
        messages = [
            {"role": "system", "content": "Tu es Askély, un assistant IA multilingue qui répond naturellement aux questions."},
            {"role": "user", "content": incoming_msg}
        ]
        response = client.chat.completions.create(model="gpt-4-turbo", messages=messages)
        answer = response.choices[0].message.content

    reply = MessagingResponse()
    reply.message(answer)
    return str(reply)

import streamlit as st
from recipes import recipes
from audiorecorder import audiorecorder
import speech_recognition as sr
import hashlib


# ---------------- PAGE ----------------

st.set_page_config(
    page_title="Livre de recettes françaises",
    page_icon="🥐"
)

st.title("🥐 Livre de recettes françaises")

st.write("Bienvenue dans notre livre de recettes !")


# ---------------- SESSION STATE ----------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_audio" not in st.session_state:
    st.session_state.last_audio = ""


# ---------------- SHOW OLD MESSAGES ----------------

for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.write(message["content"])


# ---------------- TEXT INPUT ----------------

user_input = st.chat_input(
    "💬 Que voulez-vous cuisiner ?"
)


# ---------------- VOICE INPUT ----------------

audio = audiorecorder(
    "🎤 Parler",
    "⏹️ Arrêter"
)


# ---------------- FUNCTION TO SHOW RECIPE ----------------

def show_recipe(message):

    message = message.lower()

    # Bonjour

    if "bonjour" in message:

        return "Bonjour ! Bienvenue dans notre livre de recettes."


    # Merci

    elif "merci" in message:

        return "Avec plaisir ! Bon appétit !"


    # Crêpes

    elif "crêpe" in message or "crepe" in message:

        recipe = recipes["crepes"]

        result = "🥞 " + recipe["name"] + "\n\n"

        result += "### Ingrédients\n\n"

        for ingredient in recipe["ingredients"]:

            result += "• " + ingredient + "\n"

        result += "\n### Préparation\n\n"

        for i, step in enumerate(recipe["steps"], 1):

            result += str(i) + ". " + step + "\n"

        return result


    # Ratatouille

    elif "ratatouille" in message:

        recipe = recipes["ratatouille"]

        result = "🍅 " + recipe["name"] + "\n\n"

        result += "### Ingrédients\n\n"

        for ingredient in recipe["ingredients"]:

            result += "• " + ingredient + "\n"

        result += "\n### Préparation\n\n"

        for i, step in enumerate(recipe["steps"], 1):

            result += str(i) + ". " + step + "\n"

        return result


    # Unknown

    else:

        return "Désolé, je ne connais pas encore cette recette."


# ---------------- TEXT MESSAGE ----------------

if user_input:

    # Add user's message

    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    # Get recipe

    response = show_recipe(user_input)

    # Add bot response

    st.session_state.messages.append({
        "role": "assistant",
        "content": response
    })

    # Rerun to display the new messages

    st.rerun()


# ---------------- VOICE MESSAGE ----------------

if len(audio) > 0:

    # Create a unique ID for this recording

    audio_id = hashlib.md5(
        audio.raw_data
    ).hexdigest()


    # Only process NEW recordings

    if audio_id != st.session_state.last_audio:

        st.session_state.last_audio = audio_id

        recognizer = sr.Recognizer()

        audio_data = sr.AudioData(
            audio.raw_data,
            audio.frame_rate,
            audio.sample_width
        )

        try:

            voice_text = recognizer.recognize_google(
                audio_data,
                language="fr-FR"
            )


            # Show what the user said

            st.session_state.messages.append({
                "role": "user",
                "content": "🎤 " + voice_text
            })


            # Get recipe

            response = show_recipe(voice_text)


            # Add bot response

            st.session_state.messages.append({
                "role": "assistant",
                "content": response
            })


            # Rerun

            st.rerun()


        except sr.UnknownValueError:

            st.session_state.messages.append({
                "role": "assistant",
                "content": "Désolé, je n'ai pas compris."
            })

            st.rerun()


        except sr.RequestError:

            st.session_state.messages.append({
                "role": "assistant",
                "content": "Erreur de connexion au service vocal."
            })

            st.rerun()
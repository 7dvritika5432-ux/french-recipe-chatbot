
import streamlit as st
from recipes import recipes
from audiorecorder import audiorecorder
import speech_recognition as sr
import hashlib
import unicodedata
import re
from PIL import Image

# ---------------- PAGE ----------------

st.set_page_config(
    page_title="Cuisinebot",
    page_icon="🥐",
    layout="wide"
)

st.title("🥐 Cuisinebot")
st.write("Bienvenue sur notre cuisinebot !")
st.write("Choisissez une recette ou dites son nom.")


# ---------------- SESSION STATE ----------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "current_recipe" not in st.session_state:
    st.session_state.current_recipe = None

if "ingredient_results" not in st.session_state:
    st.session_state.ingredient_results = []

if "selected_ingredient_recipe" not in st.session_state:
    st.session_state.selected_ingredient_recipe = None

if "ingredient_searched" not in st.session_state:
    st.session_state.ingredient_searched = False

if "last_audio" not in st.session_state:
    st.session_state.last_audio = ""


# ---------------- RESIZE RECIPE IMAGES ----------------

def get_sized_image(image_path):

    with Image.open(image_path) as image:

        image = image.convert("RGB")
        image.thumbnail((600, 400), Image.LANCZOS)

        canvas = Image.new("RGB", (600, 400), "white")

        x = (600 - image.width) // 2
        y = (400 - image.height) // 2

        canvas.paste(image, (x, y))

        return canvas


# ---------------- RECIPE CATEGORIES ----------------

categories = {
    "🥐 Petit-déjeuner": [
        "crepes",
        "croissants",
        "pain_perdu",
        "pain_chocolat",
        "brioche"
    ],

    "🍽️ Déjeuner": [
        "ratatouille",
        "quiche",
        "croque_monsieur",
        "salade_nicoise",
        "tian"
    ],

    "🧁 Goûter": [
        "madeleines",
        "macarons",
        "tarte_tatin",
        "eclair",
        "mousse_chocolat"
    ],

    "🍲 Dîner": [
        "soupe_oignon",
        "gratin",
        "boeuf_bourguignon",
        "coq_au_vin",
        "veloute_potimarron"
    ]
}


# ---------------- NORMALIZE TEXT ----------------

def normalize_text(message):

    message = message.lower()

    # Handle French ligatures
    message = message.replace("œ", "oe")
    message = message.replace("æ", "ae")

    message = unicodedata.normalize("NFD", message)

    message = "".join(
        character for character in message
        if unicodedata.category(character) != "Mn"
    )

    # Remove punctuation and extra spaces
    message = re.sub(r"[^a-z0-9\s]", " ", message)
    message = re.sub(r"\s+", " ", message)

    return message.strip()


# ---------------- FIND RECIPE ----------------

def get_recipe(message):

    message = normalize_text(message)

    if "bonjour" in message or "salut" in message:
        return None, "Bonjour ! Bienvenue dans notre livre de recettes."

    if "merci" in message:
        return None, "Avec plaisir ! Bon appetit !"

    recipe_keywords = [
        ("pain au chocolat", "pain_chocolat"),
        ("pain chocolat", "pain_chocolat"),
        ("pain perdu", "pain_perdu"),
        ("crepe", "crepes"),
        ("croissant", "croissants"),
        ("brioche", "brioche"),
        ("ratatouille", "ratatouille"),
        ("quiche", "quiche"),
        ("croque monsieur", "croque_monsieur"),
        ("salade nicoise", "salade_nicoise"),
        ("nicoise", "salade_nicoise"),
        ("tian", "tian"),
        ("madeleine", "madeleines"),
        ("macaron", "macarons"),
        ("tarte tatin", "tarte_tatin"),
        ("eclair", "eclair"),
        ("mousse au chocolat", "mousse_chocolat"),
        ("mousse chocolat", "mousse_chocolat"),
        ("soupe a l oignon", "soupe_oignon"),
        ("soupe", "soupe_oignon"),
        ("oignon", "soupe_oignon"),
        ("gratin", "gratin"),
        ("boeuf bourguignon", "boeuf_bourguignon"),
        ("bourguignon", "boeuf_bourguignon"),
        ("coq au vin", "coq_au_vin"),
        ("veloute de potimarron", "veloute_potimarron"),
        ("potimarron", "veloute_potimarron")
    ]

    for keyword, recipe_key in recipe_keywords:

        if keyword in message:
            return recipes[recipe_key], None

    return None, "Desole, je ne connais pas encore cette recette."


# ---------------- DISPLAY RECIPE ----------------

def display_recipe(recipe):

    st.divider()

    left, right = st.columns([2, 1])

    with left:

        st.header(recipe["name"])

        st.write("📂 **" + recipe["category"] + "**")

        st.subheader("🥣 Ingrédients")

        for ingredient in recipe["ingredients"]:
            st.write("• " + ingredient)

        st.subheader("👩‍🍳 Préparation")

        for number, step in enumerate(recipe["steps"], 1):
            st.write(str(number) + ". " + step)

        st.success("Bon appétit !")

    with right:

        st.image(
            get_sized_image(recipe["image"]),
            width="stretch"
        )


# ---------------- SMART INGREDIENT FINDER ----------------
def find_recipes_by_ingredients(user_ingredients):

    available_ingredients = [
        normalize_text(item)
        for item in user_ingredients.split(",")
        if normalize_text(item)
    ]

    results = []

    # Ignore common French ingredient description words
    ignored_words = {
        "de", "du", "des", "la", "le", "les", "d",
        "g", "kg", "ml", "l", "un", "une"
    }

    for recipe_key, recipe in recipes.items():

        recipe_ingredients = [
            normalize_text(ingredient)
            for ingredient in recipe["ingredients"]
        ]

        matched = []

        for user_item in available_ingredients:

            # Search for the complete ingredient phrase
            for recipe_ingredient in recipe_ingredients:

                recipe_words = [
                    word for word in recipe_ingredient.split()
                    if word not in ignored_words
                    and not word.isdigit()
                ]

                user_words = [
                    word for word in user_item.split()
                    if word not in ignored_words
                ]

                # Exact complete-word matching
                if user_words and all(
                    word in recipe_words
                    for word in user_words
                ):
                    matched.append(user_item)
                    break

        if matched:

            results.append({
                "recipe": recipe,
                "matched": matched,
                "score": len(matched)
            })

    results.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    return results


# =========================================================
# RECIPE MENU OR RECIPE VIEW
# =========================================================

if st.session_state.current_recipe is None:

    st.subheader("📖 Nos recettes")

    for category_name, recipe_keys in categories.items():

        st.header(category_name)

        # First row: 3 recipes
        first_row = st.columns(3)

        for index, recipe_key in enumerate(recipe_keys[:3]):

            recipe = recipes[recipe_key]

            with first_row[index]:

                st.image(
                    get_sized_image(recipe["image"]),
                    width="stretch"
                )

                if st.button(
                    recipe["name"],
                    key="button_" + recipe_key,
                    width="stretch"
                ):

                    select_recipe(recipe_key)
                    st.rerun()

        # Second row: remaining recipes
        second_row = st.columns(3)

        for index, recipe_key in enumerate(recipe_keys[3:]):

            recipe = recipes[recipe_key]

            with second_row[index]:

                st.image(
                    get_sized_image(recipe["image"]),
                    width="stretch"
                )

                if st.button(
                    recipe["name"],
                    key="button_" + recipe_key,
                    width="stretch"
                ):

                    select_recipe(recipe_key)
                    st.rerun()

else:

    # ---------------- RECIPE DETAIL VIEW ----------------

    if st.button("⬅️ Retour aux recettes"):

        st.session_state.current_recipe = None
        st.rerun()

    display_recipe(st.session_state.current_recipe)


# =========================================================
# SMART INGREDIENT FINDER
# =========================================================

st.divider()

st.subheader("🥗 Que puis-je cuisiner avec mes ingrédients ?")

st.write("Entrez les ingrédients disponibles chez vous.")

ingredient_input = st.text_input(
    "Vos ingrédients",
    placeholder="Exemple : oeufs, lait, farine"
)

if st.button("🔍 Trouver des recettes"):

    if ingredient_input.strip():

        st.session_state.ingredient_results = (
            find_recipes_by_ingredients(ingredient_input)
        )

        st.session_state.selected_ingredient_recipe = None
        st.session_state.ingredient_searched = True

    else:

        st.session_state.ingredient_results = []
        st.session_state.selected_ingredient_recipe = None
        st.session_state.ingredient_searched = False

        st.warning("Veuillez entrer vos ingrédients.")


# ---------------- DISPLAY SEARCH RESULTS ----------------

if st.session_state.ingredient_searched:

    if st.session_state.ingredient_results:

        st.success(
            str(len(st.session_state.ingredient_results))
            + " recette(s) correspondante(s) trouvée(s) !"
        )

        for item in st.session_state.ingredient_results:

            recipe = item["recipe"]

            st.write("---")

            st.subheader("🍽️ " + recipe["name"])

            st.write(
                "Ingrédients correspondants : "
                + ", ".join(item["matched"])
            )

            st.write(
                f"Correspondances : {item['score']}"
            )

            if st.button(
                "Voir la recette",
                key="ingredient_" + recipe["name"]
            ):

                if st.session_state.selected_ingredient_recipe == recipe["name"]:
                    st.session_state.selected_ingredient_recipe = None
                else:
                    st.session_state.selected_ingredient_recipe = recipe["name"]

            # Display selected recipe below its name

            if st.session_state.selected_ingredient_recipe == recipe["name"]:

                display_recipe(recipe)

    else:

        st.warning(
            "Aucune recette correspondante trouvée ! "
            "Essayez d'autres ingrédients."
        )

else:

    st.info(
        "Entrez vos ingrédients pour découvrir des recettes."
    )


# =========================================================
# CHATBOT
# =========================================================

st.divider()

st.subheader("💬 Parlez avec le livre de recettes")


# ---------------- TEXT INPUT ----------------

user_input = st.chat_input(
    "Écrivez le nom d'une recette..."
)

if user_input:

    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    recipe, response = get_recipe(user_input)

    if recipe:

        st.session_state.current_recipe = recipe

        st.session_state.messages.append({
            "role": "assistant",
            "content": "Voici la recette : " + recipe["name"]
        })

    else:

        st.session_state.messages.append({
            "role": "assistant",
            "content": response
        })

    st.rerun()


# ---------------- DISPLAY CHAT HISTORY ----------------

for message in st.session_state.messages:

    with st.chat_message(message["role"]):
        st.write(message["content"])


# =========================================================
# VOICE INPUT
# =========================================================

st.write("🎤 **Parlez en français :**")

audio = audiorecorder(
    "🎤 Parler",
    "⏹️ Arrêter"
)

if len(audio) > 0:

    audio_id = hashlib.md5(
        audio.raw_data
    ).hexdigest()

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

            st.session_state.messages.append({
                "role": "user",
                "content": "🎤 " + voice_text
            })

            recipe, response = get_recipe(voice_text)

            if recipe:

                st.session_state.current_recipe = recipe

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "Voici la recette : " + recipe["name"]
                })

            else:

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response
                })

            st.rerun()

        except sr.UnknownValueError:

            st.session_state.messages.append({
                "role": "assistant",
                "content": "Desole, je n'ai pas compris."
            })

            st.rerun()

        except sr.RequestError:

            st.session_state.messages.append({
                "role": "assistant",
                "content": "Erreur de connexion au service vocal."
            })

            st.rerun()

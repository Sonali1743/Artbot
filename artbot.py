import streamlit as st
import requests
import random
from serpapi import GoogleSearch
import time
import datetime
import re
import json
from PIL import Image
import uuid
import base64
import io
import pandas as pd
st.set_page_config(page_title="Artbot", layout="centered") #<strong>Artbot</strong>

# Configuration
#NVIDIA_API_KEY = "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"
NVIDIA_MODEL = "google/gemma-3n-e4b-it"
API_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
SERP_API_KEY = "d59c79fe8495829a1f39bdd98af40a5df3b0045dafd2848f0961737e6f4d9d42"

# Setting up Streamlit app

st.markdown("""
<div style="
    background-color: #222;
    color: #eee;
    padding: 15px 20px;
    border-radius: 10px;
    margin-bottom: 20px;
    font-size: 18px;
    font-weight: 500;
    text-align: left;
    ">
    Hi there! 👋 Welcome to <strong>Artbot</strong>, an AI-powered art chatbot built using the Google Gemma model. This chatbot answers all your art-related questions. You can customize responses using the side panel and enjoy features like:
    <ul style='margin-top: 8px;'>
        <li>Art News for updates on any art topic such as “News on Modern Art from Europe”</li>
        <li>AI Art Judge that analyzes artwork from image URLs and provides detailed critiques</li>
        <li>Generates Tweets on various art themes</li>
        <li>Artwork of the Day showcasing a new masterpiece daily</li>
        <li>An Art Quiz to test your knowledge</li>
    </ul>
    Have fun exploring. Ask away!<br><br>
    <strong>P.S.</strong> Don't forget to generate and enter your NVIDIA API key in the sidebar.
</div>
""", unsafe_allow_html=True)


# Custom styling for cleaner UI
st.markdown("""
<style>
    .stChatMessage { margin-bottom: 1.2rem; }
    .element-container:has(textarea) { margin-top: 1.5rem; }
    .stSelectbox > div { border: 1px solid #ccc; border-radius: 8px; }
    .stRadio > div { border: 1px solid #ccc; border-radius: 8px; padding: 8px; }
    .sidebar-section-title {
        color: white;
        font-weight: bold;
        font-size: 16px;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar for Chat Customization and Features
st.sidebar.markdown("""
    <style>
        .sidebar-title {
            font-size: 20px;
            font-weight: bold;
            margin-bottom: 10px;
            color: white;
        }
    </style>
    """, unsafe_allow_html=True)
    
st.sidebar.markdown("""
    <div style='font-size: 13px; color: gray; margin-bottom: 10px;'>
        Made by <a href="https://agrawalsonali22.wixstudio.com/my-portfolio" target="_blank" style="color: #bbb; text-decoration: none;">Sonali Agrawal</a>
    </div>
""", unsafe_allow_html=True)

user_api_key = st.sidebar.text_input(
    "Enter your NVIDIA API Key: (https://build.nvidia.com/google/gemma-3n-e4b-it)", 
    type="password",
    help="Provide your NVIDIA API key to use Artbot."
)
st.session_state['user_api_key'] = user_api_key.strip()

st.sidebar.markdown("<hr style='border: 1.5px solid #444;'>", unsafe_allow_html=True)

# Chat Style Customization Section
st.sidebar.markdown("<div class='sidebar-title'>🧑‍🎨 Adjust My Replies</div>", unsafe_allow_html=True)

tone = st.sidebar.selectbox("💬 Tone of Responses", ["Friendly", "Formal", "Witty and Humorous", "Poetic"])
response_length = st.sidebar.selectbox("📏 Response Length", ["Short", "Medium", "Detailed"])
expertise = st.sidebar.selectbox("🎓 Your Art Knowledge", ["Beginner", "Intermediate", "Expert"])
medium = st.sidebar.selectbox("🖌️ Art Medium Focus", ["Painting", "Sculpture/Installation", "Photography"])
st.session_state.preferences = {
    "tone": tone,
    "response_length": response_length,
    "expertise": expertise,
    "medium": medium,
}

st.sidebar.markdown("<hr style='border: 1.5px solid #444;'>", unsafe_allow_html=True)

# --- Features Section ---
st.sidebar.markdown("<div class='sidebar-title'>✨ Try a Feature</div>", unsafe_allow_html=True)

# Art News
news_topic = st.sidebar.text_input("📰 Topic for Art News", value="art news")
fetch_news = st.sidebar.button("Fetch Art News")
st.sidebar.markdown("<hr style='border: 1px dashed #888; margin-top: 4px; margin-bottom: 1px;'>", unsafe_allow_html=True)
# AI Art Judge
images = st.sidebar.text_input("Enter Image URLs (comma separated):")
art_judge = st.sidebar.button("Evaluate Artwork")
st.sidebar.markdown("<hr style='border: 1px dashed #888; margin-top: 4px; margin-bottom: 1px;'>", unsafe_allow_html=True)
# Generate Tweets
tweet_topic = st.sidebar.selectbox("🗂️ Pick a Tweet Theme:", ["General Wellness & Wellbeing", "The Power of Art",
 "Healing Through Art", "Mental Health Benefits of Art", "Healing Benefits of Colour / Colour Theory / Chromatherapy", 
 "Nervous System Healing", "The Anti-Hustle Wellness Guide", "End-of-Year Radical Self-Care", "Midday Art Wisdom", 
 "Afternoon Color & Calm Tips", "Wellness Inspiration", "Trauma and Creativity"])
tweet_generate = st.sidebar.button("📤 Create Tweets")
st.sidebar.markdown("<hr style='border: 1px dashed #888; margin-top: 4px; margin-bottom: 1px;'>", unsafe_allow_html=True)
# Artwork of the Day
show_artwork = st.sidebar.button("🖼️ Show Artwork of the Day")
st.sidebar.markdown("<hr style='border: 1px dashed #888; margin-top: 4px; margin-bottom: 1px;'>", unsafe_allow_html=True)
# Quiz Mode
quiz_click = st.sidebar.button("🎯 Start Quiz")

# System Prompt Construction
def build_system_prompt():
    prefs = st.session_state.preferences
    return f'''
    You are an assistant strictly limited to answering questions about art, including art history, artists, styles, techniques, and art movements.
    You are speaking to a(n) {prefs['expertise'].lower()} user.
    Respond in a {prefs['tone'].lower()} tone, focusing on {prefs['medium'].lower()}.
    Use recent context (e.g., artworks, artists mentioned previously) to understand follow-up questions.
    - If a question is not related to art, respond only with: I'm sorry, I can only answer questions related to art.
    - Do NOT attempt to answer any other topic.
    - Keep answers {prefs['response_length'].lower()}:
        - short = max 3 sentences
        - medium = max 6 sentences
        - detailed = max 10 sentences
    - Do not provide explanations or details outside art.
    - Customize advice and explanations based on the **art medium**:
        - For example, if the user selects "Photography", answer judging or technique questions with photo-specific concepts.
        - If the user selects "sculpture/installation", tailor language accordingly.
    - Match the **user's expertise**:
        - For **beginner**: explain in simple, jargon-free terms with clarity and approachability.
        - For **intermediate**: introduce relevant concepts and occasional technical terms.
        - For **expert**: use precise vocabulary, critical analysis, and reference relevant schools, movements, or terminology.
    '''

# Utilities

def get_headers():
    api_key = st.session_state.get('user_api_key', '')
    if not api_key:
        return None
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

# AI Art Judge
def encode_image_url_to_base64(image_url):
    response = requests.get(image_url, timeout=10)
    response.raise_for_status()
    image = Image.open(io.BytesIO(response.content)).convert("RGB")
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8"), image

def query_nvidia_vision_api(base64_image):
    prompt_text = """
    You are an experienced judge for international art competitions, with expertise in evaluating both emerging and professional artists. Your task is to analyze and critique artwork based on the following parameters, assigning each a skill category and providing justification or description.

    Skill Categories (with examples):
    Beginner - Just beginning to explore fundamentals like color mixing and brush techniques. Requires guidance at every step.
    Intermediate - Has a basic grasp of art principles and is experimenting with complexity.
    Advanced - Shows strong understanding of artistic principles and a personal voice.
    Professional/Expert - Consistently delivers polished, distinctive work with technical mastery and creative depth.

    Evaluation Parameters:
    Originality - Does the piece offer a unique or inventive take on the subject?
    Composition - Is the layout well-balanced, structured, and visually appealing?
    Color and Tone - Are color choices and tonal contrasts used effectively to convey depth and mood?
    Technical Proficiency - Does the work demonstrate mastery of brushwork, perspective, anatomy, etc.?
    Overall Impression - What lasting impact does the artwork leave on the viewer?

    Important Notes:
    Avoid defaulting to "Intermediate" for all artworks. Use the full range of skill categories.
    Do not hesitate to assign "Professional/Expert" when the execution clearly warrants it.
    Do not hesitate to assign "Beginner" when the painting has poor design and uneven brushstrokes.

    Response Format (one line per parameter):
    [Description] - Describe the painting
    [Originality] - [Skill Category] - [Comment]
    [Composition] - [Skill Category] - [Comment]
    [Color] - [Skill Category] - [Comment]
    [Technique] - [Skill Category] - [Comment]
    [Overall] - [Skill Category] - [Comment]
    """
    headers = get_headers()
    if not headers:
        st.error("Please enter your NVIDIA API key in the sidebar to use the Art Judge feature.")
        return None
    payload = {
        "model": NVIDIA_MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt_text},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }
        ]
    }

    response = requests.post(API_URL, headers=headers, json=payload)
    response.raise_for_status()
    result = response.json()
    return result.get("choices", [{}])[0].get("message", {}).get("content", "No description found.")

def query_nvidia_score(analysis_text):
    prompt = f"""
    Based on the analysis of a painting, assign it a score:

    - "Beginner: 1 to 2.5"
    - "Intermediate: 2.6 to 5"
    - "Advanced: 5.1 to 7.5"
    - "Professional/Expert: 7.6 to 10"

    Use your judgment to select a score within the appropriate range, considering the strength of the comments provided.

    Analysis:
    \"\"\"
    {analysis_text}
    \"\"\"
    Response Format:
    Score: [number]
    """
    headers = get_headers()
    if not headers:
        st.error("Please enter your NVIDIA API key in the sidebar to use the Art Judge feature.")
        return None
    payload = {
        "model": NVIDIA_MODEL,
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": prompt}]
            }
        ]
    }

    response = requests.post(API_URL, headers=headers, json=payload)
    response.raise_for_status()
    result = response.json()
    return result.get("choices", [{}])[0].get("message", {}).get("content", "No score found.")

def parse_response_to_dict(text_response):
    field_variants = {
        "Description": ["description"],
        "Originality": ["originality"],
        "Composition": ["composition"],
        "Color": ["Color", "color"],
        "Technique": ["technical proficiency", "technique", "technical"],
        "Overall": ["overall", "overall impression"]
    }

    results = {field: "" for field in field_variants}

    pattern = re.compile(r"^(.*?)[\s\-–—:]+(.*)$")

    for line in text_response.strip().split("\n"):
        line = line.strip()
        match = pattern.match(line)
        if match:
            key_raw, value = match.group(1).strip().lower(), match.group(2).lstrip("*- ").strip()
            for field, variants in field_variants.items():
                if any(variant in key_raw for variant in variants):
                    results[field] = value
                    break

    return results

def run_art_judge(image_urls):
    # Title in chat
    with st.chat_message("assistant"):
        st.markdown("🖼️ Provided Artworks", unsafe_allow_html=True)
        for url in image_urls:
            try:
                response = requests.get(url)
                image = Image.open(io.BytesIO(response.content)).convert("RGB")
                resized_image = image.resize((256, 256))
                st.image(resized_image, caption=url, use_container_width=False)
            except Exception:
                st.warning(f"⚠️ Could not load image from URL: {url}")

    # Save images section to chat history
    images_html = "### 🖼️ Provided Artworks\n\n" + "\n".join([f"![Artwork]({url})" for url in image_urls])
    st.session_state.chat_history.append({"role": "assistant", "content": images_html})

    # Run analysis
    all_results = []
    for i, url in enumerate(image_urls):
        with st.spinner(f"🔍 Analyzing Artwork {i+1}..."):
            try:
                base64_image, image_or_error = encode_image_url_to_base64(url)
                if not base64_image:
                    st.error(f"Failed to load Artwork {i+1}: {image_or_error}")
                    continue
                result_text = query_nvidia_vision_api(base64_image)
                result_dict = parse_response_to_dict(result_text)
                result_dict["Artwork"] = f"Artwork {i+1}"

                time.sleep(2)
                score_response = query_nvidia_score(result_text)
                score_match = re.search(r"Score:\s*([\d.]+)", score_response)
                result_dict["Score"] = float(score_match.group(1)) if score_match else None

                all_results.append(result_dict)
                time.sleep(2)
            except Exception as e:
                st.error(f"API Error for Artwork {i+1}: {e}")

    if all_results:
        df = pd.DataFrame(all_results)[
            ["Artwork", "Description", "Originality", "Composition", "Color", "Technique", "Overall", "Score"]
        ]

        with st.chat_message("assistant"):
            st.markdown("🎨 Art Judge Evaluation Summary", unsafe_allow_html=True)
            st.dataframe(
                df.style.set_properties(**{
                    'font-size': '16px',
                    'text-align': 'left',
                }),
                use_container_width=True
            )

        # Save table as Markdown to chat history
        table_md = "### 🎨 Art Judge Evaluation Summary\n\n```text\n" + df.to_markdown(index=False) + "\n```"
        st.session_state.chat_history.append({"role": "assistant", "content": table_md})

# Tweets
def generate_tweets(topic):
    prompt = f"""
    # CONTEXT #
    You are an agent that knows everything about Art. 
    You are inspired by artists like Michelangelo, Warhol, Vonnegut, and Salvador Dali.
    You are a champion of the Arts.
    You think differently, out-of-the-box and are one of the original thinkers of this era.

    #############

    # OBJECTIVE #
    Generate 5 tweets for twitter on the {topic}. Please keep in mind below points:
    1. Fun personality mix: holistic + a little Hunter S Thompson + a little Kurt Vonnegut.
    2. Make them short, punchy and scroll-stoppers.

    #############

    # STYLE #

    Follow the simple writing style aimed at common people. Use easy to understand language.
    Keep it insightful, emotional, and free-flowing.

    #############

    # TONE #

    Use uplifting, therapeutic, and mindful tone.

    #############

    # AUDIENCE #
    Tailor the post toward common people, artists and people interested in arts.

    #############

    # RESPONSE #
    Be concise and succinct in your response yet impactful. Where appropriate, use
    appropriate emojies.
    """
    headers = get_headers()
    if not headers:
        st.error("Please enter your NVIDIA API key in the sidebar to use the Art Judge feature.")
        return None
    payload = {
        "model": NVIDIA_MODEL,
        "messages": [{"role": "user", "content": prompt}]
    }

    response = requests.post(API_URL, headers=headers, json=payload)
    response.raise_for_status()
    result = response.json()
    return result.get("choices", [{}])[0].get("message", {}).get("content", "No response generated.")

# Quiz
def generate_quiz_batch():
    prompt = """
    Generate 5 unique multiple-choice quiz questions about art.
    Each question should have:
    - A question string
    - 4 answer options
    - One correct answer

    Return the result as a JSON list of 5 objects, like this:

    [
      {
        "question": "Which artist painted the Mona Lisa?",
        "options": ["Leonardo da Vinci", "Vincent van Gogh", "Claude Monet", "Pablo Picasso"],
        "answer": "Leonardo da Vinci"
      },
      ...
    ]
    """
    headers = get_headers()
    if not headers:
        st.error("Please enter your NVIDIA API key in the sidebar to use the Art Judge feature.")
        return None
    payload = {
        "model": NVIDIA_MODEL,
        "messages": [{"role": "user", "content": prompt}]
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()
        raw_text = response.json()["choices"][0]["message"]["content"].strip()

        # Strip Markdown formatting if any
        if raw_text.startswith("```json"):
            raw_text = raw_text.strip("```json").strip("```").strip()
        elif raw_text.startswith("```"):
            raw_text = raw_text.strip("```").strip()

        # Parse JSON safely
        all_questions = json.loads(raw_text)

        if not isinstance(all_questions, list):
            raise ValueError("Parsed result is not a list")

        # Filter out duplicates using session state
        if "past_quiz_questions" not in st.session_state:
            st.session_state.past_quiz_questions = []

        seen = st.session_state.past_quiz_questions
        unique_questions = [q for q in all_questions if q.get("question") not in seen and all(k in q for k in ["question", "options", "answer"])]

        # Update seen questions
        st.session_state.past_quiz_questions += [q["question"] for q in unique_questions]

        return unique_questions

    except Exception as e:
        st.error(f"❌ Quiz generation failed: {e}")
        return []

@st.cache_data(show_spinner=False)
def fetch_recent_art_news(user_query, max_articles=5):
    """Fetch recent art news using SerpAPI."""
    search_params = {
        "engine": "google",
        "q": f"{user_query} after:7d",
        "num": max_articles,
        "api_key": SERP_API_KEY,
        "tbm": "nws"
    }
    try:
        search = GoogleSearch(search_params)
        results = search.get_dict()
        news_results = results.get("news_results", [])
        articles = [{
            "title": art.get("title", ""),
            "link": art.get("link", ""),
            "summary": art.get("snippet", ""),
            "source": art.get("source", ""),
            "date": art.get("date", "")
        } for art in news_results[:max_articles]]
        return articles
    except Exception as e:
        print(f"Error fetching news: {e}")
        return []

def summarize_and_filter_news(user_query, article):
    prompt = f"""
    You are an insightful art commentator. Given the user's request: '{user_query}', write a concise, warm, and relevant summary of this news article. Only summarize if it is relevant to the user's request. End with a hyperlink labeled 'Read more' pointing to the actual URL. If not relevant, return an empty string.

    Title: {article['title']}
    Summary: {article['summary']}
    URL: {article['link']}
    """
    headers = get_headers()
    if not headers:
        st.error("Please enter your NVIDIA API key in the sidebar to use the Art Judge feature.")
        return None
    payload = {
        "model": NVIDIA_MODEL,
        "messages": [{"role": "user", "content": prompt}]
    }
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()
        content = response.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        return content
    except Exception as e:
        return f"Error summarizing article: {e}"

@st.cache_data(show_spinner=False)
def get_random_met_artwork():
    met_api = "https://collectionapi.metmuseum.org/public/collection/v1"
    # Use today's date as seed for consistent artwork per day
    today_seed = int(datetime.datetime.now().strftime("%Y%m%d"))
    random.seed(today_seed)
    id_resp = requests.get(f"{met_api}/search", params={
        "hasImages": True,
        "departmentId": 11,
        "q": "painting"
    })
    object_ids = id_resp.json().get("objectIDs", [])
    if not object_ids:
        return None
    obj_id = random.choice(object_ids)
    obj_data = requests.get(f"{met_api}/objects/{obj_id}").json()
    return {
        "title": obj_data.get("title", "Untitled"),
        "artist": obj_data.get("artistDisplayName", "Unknown Artist"),
        "image_url": obj_data.get("primaryImageSmall", ""),
        "object_date": obj_data.get("objectDate", ""),
        "medium": obj_data.get("medium", ""),
        "credit_line": obj_data.get("creditLine", ""),
        "description_data": {
            "title": obj_data.get("title", ""),
            "artist": obj_data.get("artistDisplayName", ""),
            "medium": obj_data.get("medium", ""),
            "date": obj_data.get("objectDate", "")
        }
    }

def describe_artwork_with_nvidia(data):
    prompt = f"""
    You are an expert in art interpretation and storytelling.
    Write a 2-3 sentence, poetic and emotionally engaging description of the following artwork for a general audience. Keep it warm, uplifting, and descriptive.

    Title: {data['title']}
    Artist: {data['artist']}
    Medium: {data['description_data']['medium']}
    Date: {data['description_data']['date']}
    """
    headers = get_headers()
    if not headers:
        st.error("Please enter your NVIDIA API key in the sidebar to use the Art Judge feature.")
        return None
    payload = {
        "model": NVIDIA_MODEL,
        "messages": [{"role": "user", "content": prompt}]
    }
    response = requests.post(API_URL, headers=headers, json=payload)
    response.raise_for_status()
    result = response.json()
    return result.get("choices", [{}])[0].get("message", {}).get("content", "No description available.")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = [{"role": "system", "content": build_system_prompt()}]

if "quiz_batch" not in st.session_state:
    st.session_state.quiz_batch = []

if "quiz_answers" not in st.session_state:
    st.session_state.quiz_answers = {}

if "past_quiz_questions" not in st.session_state:
    st.session_state.past_quiz_questions = []

past_questions = st.session_state.past_quiz_questions
past_questions_text = "\n".join([f"- {q}" for q in past_questions[-20:]])  # Limit to last 20 for brevity

# Sidebar features
# Generate Tweets
if tweet_generate:
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("✍️ Crafting tweets...")
    try:
        tweets_output = generate_tweets(tweet_topic)
        if tweets_output:
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": f"### 🐦 Generated Tweets on *{tweet_topic}*:\n\n" + tweets_output
            })
        else:
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": "No tweets could be generated. Please try again!"
            })
    except Exception as e:
        st.error(f"Error generating tweets: {e}")
    st.rerun()

# Quiz mode
if quiz_click:
    batch = generate_quiz_batch()
    if not batch:
        st.warning("No new quiz questions could be generated.")
    else:
        st.session_state.quiz_batch = batch
        st.session_state.quiz_index = 0
        quiz = batch[0]
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": f"🎯 **Quiz Time!**\n\n**{quiz['question']}**\n\nOptions:\n" +
                       "\n".join([f"- {opt}" for opt in quiz['options']])
        })
        st.rerun()

# Artwork of the Day
if show_artwork:
    art = get_random_met_artwork()
    if art and art["image_url"]:
        description = describe_artwork_with_nvidia(art)
        st.session_state["art"] = art
        art_message = f"""
        ![{art['title']}]({art['image_url']})

        **{art['title']}**  
        *by {art['artist']}*

        {description}
        """
        art_context = f"""
        Artwork Context:
        Title: {art['title']}
        Artist: {art['artist']}
        Medium: {art['medium']}
        Date: {art['object_date']}
        """
        st.session_state.chat_history.append({"role": "assistant", "content": art_message})
        st.session_state["art_context"] = art_context
    else:
        st.session_state.chat_history.append({"role": "assistant", "content": "Couldn't load an artwork today. Please try again later."})

# Art News
if fetch_news:
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("⏳ Fetching news...")

    articles = fetch_recent_art_news(news_topic)

    if not articles:
        response = "Sorry, I couldn't find any recent art news."
        st.session_state.chat_history.append({"role": "assistant", "content": response})
    else:
        summarized_news = []
        for entry in articles:
            rewritten = summarize_and_filter_news(news_topic, entry)
            if rewritten:
                summarized_news.append(rewritten)

        if summarized_news:
            combined_news = "### 📰 Latest Art News\n\n" + "\n\n".join(summarized_news)
            st.session_state.chat_history.append({"role": "assistant", "content": combined_news})
    st.rerun()

# Display conversation except system prompt
for msg in st.session_state.chat_history[1:]:
    role_name = "Human" if msg["role"] == "user" else "Artbot"
    with st.chat_message(msg["role"]):
        st.markdown(msg['content'])

# Run AI Art Judge if button clicked and URLs provided
if art_judge and images:
    image_urls = [url.strip() for url in images.split(",") if url.strip()]
    if image_urls:
        result_md = run_art_judge(image_urls)
        if result_md:
            st.markdown(result_md)
    else:
        st.warning("Please enter valid image URLs separated by commas.")

# Show answer input if quiz is active
if "quiz_batch" in st.session_state and "quiz_index" in st.session_state:
    index = st.session_state.quiz_index
    if index < len(st.session_state.quiz_batch):
        quiz = st.session_state.quiz_batch[index]
        user_answer = st.radio("Your answer:", quiz["options"], key=f"quiz_{index}")
        if st.button("Submit Answer", key=f"submit_{index}"):
            if user_answer == quiz["answer"]:
                result = "✅ Correct!"
            else:
                result = f"❌ Incorrect. The correct answer is: **{quiz['answer']}**"
            st.session_state.chat_history.append({"role": "assistant", "content": result})
            st.session_state.quiz_index += 1
            if st.session_state.quiz_index < len(st.session_state.quiz_batch):
                next_q = st.session_state.quiz_batch[st.session_state.quiz_index]
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": f"**Next Question:**\n\n**{next_q['question']}**\n\nOptions:\n" +
                               "\n".join([f"- {opt}" for opt in next_q['options']])
                })
            else:
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": "🏁 You've completed all 5 quiz questions! Click the button again to try more."
                })
            st.rerun()

if st.sidebar.button("♻️ Reset Quiz History"):
    st.session_state.pop("past_quiz_questions", None)
    st.sidebar.success("Quiz history cleared!")

user_input = st.chat_input("Ask me anything about art...")

if user_input:
    # Append user message
    st.session_state.chat_history[0] = {"role": "system", "content": build_system_prompt()}
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)
    
    art_context = st.session_state.get("art_context", "")
    cleaned_context = art_context
    if art_context:
        cleaned_context = re.sub(r'!\[.*?\]\(.*?\)', '', art_context)
        cleaned_context = "\n".join([line.strip() for line in cleaned_context.strip().splitlines() if line.strip()])
    if cleaned_context:
        system_msg = {"role": "system", "content": build_system_prompt() + "\n" + cleaned_context}
    else:
        system_msg = {"role": "system", "content": build_system_prompt()}
    
    headers = get_headers()
    if not headers:
        st.error("Please enter your NVIDIA API key in the sidebar to use the Art Judge feature.")
    else:
        payload = {
            "model": NVIDIA_MODEL,
            "messages": [system_msg, {"role": "user", "content": user_input}]
        }
        try:
            response = requests.post(API_URL, headers=headers, json=payload)
            response.raise_for_status()
        except Exception as e:
            st.error(f"API Error: {e}")
            st.code(str(payload))
            raise
        reply = response.json()["choices"][0]["message"]["content"].strip()
        assistant_response = ""
        with st.chat_message("assistant") as msg_box:
            message_placeholder = st.empty()
            for chunk in reply.split():
                assistant_response += chunk + " "
                message_placeholder.markdown(assistant_response + "▌")
                time.sleep(0.03)
            message_placeholder.markdown(assistant_response.strip())
        st.session_state.chat_history.append({"role": "assistant", "content": assistant_response.strip()})
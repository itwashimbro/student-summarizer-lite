from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from openai import OpenAI
import requests
import uvicorn import os

# OpenRouter Client
client = OpenAI(
    api_key = os.getenv("OPENAI_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

# FastAPI App
app = FastAPI()

# HTML Frontend
HTML = """
<!DOCTYPE html>
<html>

<head>

    <title>Student AI</title>

    <style>

        body {
            font-family: Arial;
            background: linear-gradient(to right, #141e30, #243b55);
            padding: 40px;
            color: white;
        }

        .container {
            max-width: 1000px;
            margin: auto;
            background: rgba(255,255,255,0.08);
            backdrop-filter: blur(10px);
            padding: 30px;
            border-radius: 20px;
            box-shadow: 0px 0px 25px rgba(0,0,0,0.3);
        }

        h1 {
            text-align: center;
            font-size: 40px;
            margin-bottom: 30px;
        }

        .tabs {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-bottom: 25px;
        }

        .tabs button {
            padding: 12px 24px;
            border: none;
            border-radius: 12px;
            background: #00c6ff;
            color: white;
            cursor: pointer;
            font-size: 16px;
            transition: 0.3s;
        }

        .tabs button:hover {
            transform: scale(1.05);
            background: #0072ff;
        }

        .tabcontent {
            display: none;
            animation: fadeIn 0.4s ease;
        }

        textarea {
            width: 100%;
            height: 250px;
            padding: 18px;
            border-radius: 15px;
            border: none;
            outline: none;
            font-size: 16px;
            resize: none;
            background: rgba(255,255,255,0.9);
        }

        input[type="file"] {
            margin-bottom: 20px;
            color: white;
        }

        button.action {
            margin-top: 20px;
            padding: 14px 28px;
            border: none;
            border-radius: 12px;
            background: linear-gradient(to right, #00c6ff, #0072ff);
            color: white;
            cursor: pointer;
            font-size: 16px;
            transition: 0.3s;
        }

        button.action:hover {
            transform: scale(1.05);
        }

        .output {
            margin-top: 25px;
            background: rgba(255,255,255,0.12);
            padding: 25px;
            border-radius: 15px;
            white-space: pre-wrap;
            line-height: 1.7;
            box-shadow: 0px 0px 12px rgba(0,0,0,0.2);
        }

        @keyframes fadeIn {

            from {
                opacity: 0;
                transform: translateY(10px);
            }

            to {
                opacity: 1;
                transform: translateY(0px);
            }

        }

    </style>

</head>

<body>

    <div class="container">

        <h1>🤖 Student AI Assistant</h1>

        <div class="tabs">

            <button onclick="openTab('summarizer')">📚 Summarizer</button>

            <button onclick="openTab('chatbot')">💬 Chat AI</button>

        </div>

        <!-- Summarizer -->
        <div id="summarizer" class="tabcontent">

            <h2>📖 Study Summarizer</h2>

            <input type="file" id="fileInput">

            <textarea id="summaryContent" placeholder="Paste study material here..."></textarea>

            <br>

            <button class="action" onclick="summarizeText()">Generate Summary</button>

            <div class="output" id="summaryResult"></div>

        </div>

        <!-- Chat -->
        <div id="chatbot" class="tabcontent">

            <h2>💡 Ask AI Tutor</h2>

            <textarea id="chatContent" placeholder="Ask anything..."></textarea>

            <br>

            <button class="action" onclick="chatWithAI()">Send Message</button>

            <div class="output" id="chatResult"></div>

        </div>

    </div>

    <script>

        // Open Tabs
        function openTab(tabName) {

            const tabs = document.getElementsByClassName("tabcontent");

            for (let i = 0; i < tabs.length; i++) {

                tabs[i].style.display = "none";

            }

            document.getElementById(tabName).style.display = "block";
        }

        // Default Tab
        openTab("summarizer");

        // File Upload
        document.getElementById("fileInput").addEventListener("change", function(event) {

            const file = event.target.files[0];

            if (!file) return;

            const reader = new FileReader();

            reader.onload = function(e) {

                document.getElementById("summaryContent").value = e.target.result;

            };

            reader.readAsText(file);

        });

        // Summarizer
        async function summarizeText() {

            const text = document.getElementById("summaryContent").value;

            document.getElementById("summaryResult").innerHTML = "⏳ Generating summary...";

            const response = await fetch("/summarize", {

                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    text: text
                })

            });

            const data = await response.json();

            document.getElementById("summaryResult").innerHTML = data.summary;

        }

        // Chat
        async function chatWithAI() {

            const text = document.getElementById("chatContent").value;

            document.getElementById("chatResult").innerHTML = "🤔 Thinking...";

            const response = await fetch("/chat", {

                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    text: text
                })

            });

            const data = await response.json();

            document.getElementById("chatResult").innerHTML = data.reply;

        }

    </script>

</body>

</html>
"""

# Request Model
class Content(BaseModel):
    text: str


# Internet Search
def internet_search(query):

    url = f"https://api.duckduckgo.com/?q={query}&format=json"

    try:

        response = requests.get(url)

        data = response.json()

        abstract = data.get("Abstract", "")

        related = data.get("RelatedTopics", [])

        extra = ""

        for item in related[:5]:

            if isinstance(item, dict):

                extra += item.get("Text", "") + "\\n"

        return abstract + "\\n" + extra

    except:

        return ""


# Home Page
@app.get("/", response_class=HTMLResponse)
def home():

    return HTML


# Summarizer API
@app.post("/summarize")
def summarize(data: Content):

    web_info = internet_search(data.text[:100])

    prompt = f'''
You are an AI assistant for students.

Summarize the study material clearly.

STUDY MATERIAL:
{data.text}

INTERNET INFO:
{web_info}
'''

    response = client.chat.completions.create(

        model="openai/gpt-3.5-turbo-0613",

        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]

    )

    result = response.choices[0].message.content

    return JSONResponse({
        "summary": result
    })


# Chat API
@app.post("/chat")
def chat(data: Content):

    response = client.chat.completions.create(

        model="openai/gpt-3.5-turbo-0613",

        messages=[
            {
                "role": "system",
                "content": "You are a helpful AI tutor for students."
            },
            {
                "role": "user",
                "content": data.text
            }
        ]

    )

    result = response.choices[0].message.content

    return JSONResponse({
        "reply": result
    })


# Run App
if __name__ == "__main__":

    uvicorn.run(app, host="0.0.0.0", port=8000)

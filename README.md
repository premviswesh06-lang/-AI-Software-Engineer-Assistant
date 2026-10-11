# AI Software Engineer Assistant

## Folder layout
```
AI-Software-Engineer-Assistant
├── app.py
├── requirements.txt
├── .env                  (you create this, see step 3)
├── serviceAccountKey.json (you add this, see step 4)
└── templates
    └── index.html
```

## How to run
1. Install Python from python.org (tick "Add Python to PATH").
2. Open the folder in VS Code, then Terminal > New Terminal, and run:
   `pip install -r requirements.txt`
3. Copy `.env.example`, rename the copy to `.env`, and paste your Groq key
   (free at console.groq.com).
4. Add your Firebase `serviceAccountKey.json` to the main folder
   (Firebase console > Project settings > Service accounts > Generate new private key).
   Also create a Firestore database (test mode) in that Firebase project.
5. Run: `python app.py`
6. Open http://127.0.0.1:5000

Demo without keys: double-click `templates/index.html` (sample answers only).
Never share or upload `.env` or `serviceAccountKey.json` publicly.

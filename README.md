# Disaster Management RAG Chatbot

A multilingual disaster management chatbot that uses RAG (Retrieval Augmented Generation) to provide accurate information about disaster management procedures, emergency protocols, safety measures, risk assessment, and relief operations.

## Features

- 🧠 Gemini Pro for text generation
- 🔍 Pinecone for vector storage
- ⚡ LangChain for the RAG pipeline
- 🌐 Multilingual support (English & Sindhi)
- 📄 PDF and text download options
- 💬 Modern, minimalistic UI

## Installation

1. Clone the repository:
```bash
git clone https://github.com/AryanQureshi/rag-chatbot.git
cd rag-chatbot
```

2. Install the required packages:
```bash
pip install -r requirements.txt
```

3. **IMPORTANT: Remove deprecated Pinecone plugins**:
```bash
pip uninstall -y pinecone-plugin-inference pinecone-plugin-interface
```

4. Create a `.env` file with your API keys:
```
PINECONE_API_KEY=your_pinecone_api_key
GOOGLE_API_KEY=your_google_api_key
```

5. Run the app:
```bash
streamlit run app.py
```

## Deployment Notes

When deploying to Streamlit Cloud, make sure to:

1. Add your API keys to the Streamlit Secrets management
2. Ensure you're using the latest version of Pinecone (>= 6.0.0)
3. Remove any deprecated Pinecone plugins from your environment

## Troubleshooting

If you encounter the error `pinecone.deprecated_plugins.DeprecatedPluginError`, follow these steps:

1. Make sure you're using the latest Pinecone package:
   ```bash
   pip install --upgrade pinecone
   ```

2. Remove any deprecated Pinecone plugins:
   ```bash
   pip uninstall -y pinecone-plugin-inference pinecone-plugin-interface
   ```

3. Restart your application

## License

MIT

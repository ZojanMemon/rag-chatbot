import streamlit as st
import google.generativeai as genai
from langchain_core.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone as PineconeClient
from datetime import datetime
from fpdf import FPDF
import io
import textwrap
from gtts import gTTS
import os
import tempfile
import base64

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

def text_to_speech(text):
    """Convert text to speech using gTTS and return audio HTML."""
    try:
        tts = gTTS(text=text, lang='en', slow=False)
        fp = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        tts.save(fp.name)
        audio_file = open(fp.name, "rb")
        audio_bytes = audio_file.read()
        audio_file.close()
        os.unlink(fp.name)
        return base64.b64encode(audio_bytes).decode()
    except Exception as e:
        st.error(f"Error generating speech: {str(e)}")
        return None

def initialize_rag():
    """Initialize RAG components"""
    try:
        PINECONE_API_KEY = st.secrets["PINECONE_API_KEY"]
        GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
        
        # Initialize Pinecone
        pc = PineconeClient(api_key=PINECONE_API_KEY)
        index = pc.Index("disaster-management")
        
        # Initialize Google Generative AI
        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel('gemini-pro')
        
        # Initialize embeddings model
        embeddings_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        return index, model, embeddings_model
    except Exception as e:
        st.error(f"Error initializing RAG: {str(e)}")
        return None, None, None

def get_response(query, index, model, embeddings_model):
    """Get response using RAG"""
    try:
        # Get query embedding
        query_embedding = embeddings_model.encode(query).tolist()
        
        # Query Pinecone
        results = index.query(vector=query_embedding, top_k=3, include_metadata=True)
        
        # Extract relevant context
        context = ""
        for match in results.matches:
            if match.metadata and 'text' in match.metadata:
                context += match.metadata['text'] + "\n\n"
        
        # Create prompt with context
        prompt = f"""You are a helpful disaster management assistant. Use the following context to answer the question. 
        If you cannot find the answer in the context, say so and provide a general response.
        
        Context: {context}
        
        Question: {query}
        
        Answer:"""
        
        # Generate response
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        st.error(f"Error getting response: {str(e)}")
        return "I apologize, but I encountered an error while processing your request."

def get_general_response(query):
    """Get general response for non-disaster related queries"""
    if any(greeting in query.lower() for greeting in ['hi', 'hello', 'hey']):
        return "Hello! I'm your disaster management assistant. How can I help you today?"
    return "I'm specifically trained to help with disaster management related questions. Could you please ask something related to disaster management?"

def export_chat_to_pdf():
    """Export chat history to PDF"""
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        
        # Add title
        pdf.cell(200, 10, txt="Chat History", ln=1, align='C')
        pdf.ln(10)
        
        # Add timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        pdf.cell(200, 10, txt=f"Generated on: {timestamp}", ln=1, align='L')
        pdf.ln(10)
        
        # Add chat messages
        for message in st.session_state.messages:
            role = "User" if message["role"] == "user" else "Assistant"
            pdf.cell(200, 10, txt=f"{role}:", ln=1, align='L')
            
            # Wrap text to fit in PDF
            wrapped_text = textwrap.fill(message["content"], width=80)
            for line in wrapped_text.split('\n'):
                pdf.cell(200, 10, txt=line, ln=1, align='L')
            pdf.ln(5)
        
        return pdf.output(dest='S').encode('latin1')
    except Exception as e:
        st.error(f"Error generating PDF: {str(e)}")
        return None

def export_chat_to_text():
    """Export chat history to text"""
    try:
        text = "Chat History\n\n"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        text += f"Generated on: {timestamp}\n\n"
        
        for message in st.session_state.messages:
            role = "User" if message["role"] == "user" else "Assistant"
            text += f"{role}: {message['content']}\n\n"
        
        return text
    except Exception as e:
        st.error(f"Error generating text: {str(e)}")
        return None

def main():
    st.title("Disaster Management Chatbot")
    
    # Initialize RAG components
    index, model, embeddings_model = initialize_rag()
    
    if not all([index, model, embeddings_model]):
        st.error("Failed to initialize required components. Please check your API keys and try again.")
        return
    
    # Sidebar with export options
    with st.sidebar:
        st.title("Export Options")
        
        if st.button("Export as PDF"):
            pdf_data = export_chat_to_pdf()
            if pdf_data:
                st.download_button(
                    label="Download PDF",
                    data=pdf_data,
                    file_name="chat_history.pdf",
                    mime="application/pdf"
                )
        
        if st.button("Export as Text"):
            text_data = export_chat_to_text()
            if text_data:
                st.download_button(
                    label="Download Text",
                    data=text_data,
                    file_name="chat_history.txt",
                    mime="text/plain"
                )
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant":
                audio_file = text_to_speech(message["content"])
                if audio_file:
                    st.audio(f"data:audio/mpeg;base64,{audio_file}")
    
    # Chat input
    if prompt := st.chat_input("Ask your question here"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            if any(word in prompt.lower() for word in ['disaster', 'emergency', 'crisis', 'catastrophe']):
                response_text = get_response(prompt, index, model, embeddings_model)
            else:
                response_text = get_general_response(prompt)
            
            st.markdown(response_text)
            
            # Add audio playback for response
            audio_file = text_to_speech(response_text)
            if audio_file:
                st.audio(f"data:audio/mpeg;base64,{audio_file}")
            
            st.session_state.messages.append({"role": "assistant", "content": response_text})

if __name__ == "__main__":
    main()
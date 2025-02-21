import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
import google.generativeai as genai
from langchain_core.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone as PineconeClient
from datetime import datetime
from fpdf import FPDF
import io
import textwrap
from gtts import gTTS
import base64
import os
import tempfile

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

def text_to_speech(text):
    """Convert text to speech using gTTS and return audio HTML."""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
            tts = gTTS(text=text, lang='en', slow=False)
            tts.save(fp.name)
            return fp.name
    except Exception as e:
        st.error(f"Error generating speech: {str(e)}")
        return None

def is_general_chat(query):
    """Check if the query is a general chat or greeting."""
    general_phrases = [
        'hi ', 'hello ', 'hey ', 'good morning', 'good afternoon', 'good evening',
        'how are you', 'what\'s up', 'nice to meet you', 'thanks', 'thank you',
        'bye', 'goodbye', 'see you', 'who are you', 'what can you do'
    ]
    # Add spaces around the query to ensure we match whole words
    query = f" {query.lower()} "
    return any(f" {phrase} " in query for phrase in general_phrases)

def get_general_response(query):
    """Generate appropriate responses for general chat."""
    query_lower = query.lower()
    
    if any(greeting in query_lower for greeting in ['hi', 'hello', 'hey']):
        return "Hello! I'm your disaster management assistant. How can I help you today?"
    
    elif any(time in query_lower for time in ['good morning', 'good afternoon', 'good evening']):
        return f"Thank you, {query}! I'm here to help you with disaster management related questions."
    
    elif 'how are you' in query_lower:
        return "I'm functioning well, thank you for asking! I'm ready to help you with disaster management information."
    
    elif 'thank' in query_lower:
        return "You're welcome! Feel free to ask any questions about disaster management."
    
    elif 'bye' in query_lower or 'goodbye' in query_lower:
        return "Goodbye! If you have more questions about disaster management later, feel free to ask."
    
    elif 'who are you' in query_lower:
        return "I'm a specialized chatbot designed to help with disaster management information and procedures. I can answer questions about emergency protocols, safety measures, and disaster response strategies."
    
    elif 'what can you do' in query_lower:
        return """I can help you with various disaster management topics, including:
- Emergency response procedures
- Disaster preparedness
- Safety protocols
- Risk assessment
- Relief operations
- And more related to disaster management

Feel free to ask specific questions about these topics!"""
    
    else:
        return "I'm specialized in disaster management topics. While I can't help with general topics, I'd be happy to answer any questions about disaster management, emergency procedures, or safety protocols."

def initialize_rag():
    try:
        # API Keys from secrets
        PINECONE_API_KEY = st.secrets["PINECONE_API_KEY"]
        GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
        
        if not GOOGLE_API_KEY or not PINECONE_API_KEY:
            st.error("Please set up API keys in Streamlit Cloud secrets")
            st.stop()
            
        genai.configure(api_key=GOOGLE_API_KEY)

        # Initialize Pinecone
        pc = PineconeClient(api_key=PINECONE_API_KEY)

        # Initialize embeddings
        try:
            embeddings = HuggingFaceEmbeddings(
                model_name='all-MiniLM-L6-v2',
                model_kwargs={'device': 'cpu'},
                encode_kwargs={
                    'normalize_embeddings': True,
                    'batch_size': 32
                }
            )
        except Exception as e:
            st.error(f"Error initializing embeddings: {str(e)}")
            st.stop()

        # Initialize vector store
        index_name = "pdfinfo"
        vectorstore = PineconeVectorStore(
            index=pc.Index(index_name),
            embedding=embeddings,
            text_key="text"
        )

        # Create Gemini LLM
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            temperature=0.1,
            google_api_key=GOOGLE_API_KEY,
            max_retries=3,
            timeout=30,
            max_output_tokens=2048
        )

        # Create the QA chain with improved prompt
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vectorstore.as_retriever(search_kwargs={"k": 4}),
            return_source_documents=False,
            chain_type_kwargs={
                "prompt": PromptTemplate(
                    template="""You are a knowledgeable disaster management assistant. Use the following guidelines to answer questions:

1. If the context contains relevant information:
   - Provide a detailed and comprehensive answer using the information
   - Include specific details and procedures from the source
   - Structure the response in a clear, readable format
   - Use professional and precise language

2. If the context does NOT contain sufficient information:
   - Provide a general, informative response based on common disaster management principles
   - Be honest about not having specific details
   - Offer to help with related topics that are within your knowledge base
   - Never make up specific numbers or procedures
   - Guide the user towards asking more specific questions about disaster management

Context: {context}

Question: {question}

Response (remember to be natural and helpful):""",
                    input_variables=["context", "question"],
                )
            }
        )
        return qa_chain, llm
    except Exception as e:
        st.error(f"Error initializing RAG system: {str(e)}")
        st.stop()

def create_chat_pdf():
    """Generate a PDF file of chat history with proper formatting."""
    pdf = FPDF()
    pdf.add_page()
    
    # Set up the PDF
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Disaster Management Chatbot - Conversation Log", ln=True, align='C')
    pdf.ln(10)
    
    # Add content
    pdf.set_font("Arial", size=12)
    for message in st.session_state.messages:
        # Role header
        pdf.set_font("Arial", "B", 12)
        role = "Bot" if message["role"] == "assistant" else "User"
        pdf.cell(0, 10, f"{role}:", ln=True)
        
        # Message content with proper wrapping
        pdf.set_font("Arial", size=11)
        text = message["content"]
        wrapped_text = textwrap.fill(text, width=85)
        for line in wrapped_text.split('\n'):
            pdf.cell(0, 7, line, ln=True)
        pdf.ln(5)
    
    return pdf.output(dest='S').encode('latin1')

def create_chat_text():
    """Generate a formatted text file of chat history."""
    output = io.StringIO()
    output.write("Disaster Management Chatbot - Conversation Log\n")
    output.write("="*50 + "\n\n")
    
    for message in st.session_state.messages:
        role = "Bot" if message["role"] == "assistant" else "User"
        output.write(f"{role}:\n")
        output.write(f"{message['content']}\n")
        output.write("-"*50 + "\n\n")
    
    text_data = output.getvalue()
    output.close()
    return text_data

def main():
    # Page config
    st.set_page_config(
        page_title="Disaster Management RAG Chatbot",
        page_icon="🤖",
        layout="wide"
    )
    
    # Header
    st.title("Disaster Management RAG Chatbot 🤖")
    st.markdown("""
    This chatbot can answer questions about disaster management based on the provided documentation.
    """)

    try:
        # Initialize RAG system
        qa_chain, llm = initialize_rag()

        # Create two columns
        col1, col2 = st.columns([2, 1])

        with col1:
            # Display chat history
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
                    # Add audio playback for assistant responses
                    if message["role"] == "assistant":
                        audio_file = text_to_speech(message["content"])
                        if audio_file:
                            st.audio(audio_file)
                            os.unlink(audio_file)

            # Chat input
            if prompt := st.chat_input("Ask your question here"):
                # Display user message
                with st.chat_message("user"):
                    st.markdown(prompt)
                st.session_state.messages.append({"role": "user", "content": prompt})

                # Display assistant response
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        if is_general_chat(prompt):
                            response_text = get_general_response(prompt)
                        else:
                            response = qa_chain({"query": prompt})
                            response_text = response['result']
                        st.markdown(response_text)
                        # Add audio playback for response
                        audio_file = text_to_speech(response_text)
                        if audio_file:
                            st.audio(audio_file)
                            os.unlink(audio_file)
                st.session_state.messages.append({"role": "assistant", "content": response_text})

        # Sidebar with information
        with col2:
            st.title("About")
            st.markdown("""
            ### Features
            This chatbot uses:
            - 🧠 Gemini Pro for text generation
            - 🔊 Text-to-speech for responses
            - 🔍 Pinecone for vector storage
            - ⚡ LangChain for the RAG pipeline
            
            ### Topics
            You can ask questions about:
            - 📋 Disaster management procedures
            - 🚨 Emergency protocols
            - 🛡️ Safety measures
            - 📊 Risk assessment
            - 🏥 Relief operations
            
            ### Tips
            - Ask specific questions
            - Listen to responses with audio playback
            - Use clear, simple language
            """)

            # Add buttons for chat management
            st.markdown("### Chat Management")
            col_clear, col_download_text, col_download_pdf = st.columns(3)
            
            with col_clear:
                if st.button("Clear Chat"):
                    st.session_state.messages = []
                    st.rerun()
            
            with col_download_text:
                if st.download_button(
                    label="Download Text",
                    data=create_chat_text(),
                    file_name=f"chat_history_{datetime.now().strftime('%Y%m%d')}.txt",
                    mime="text/plain"
                ):
                    st.success("Chat history downloaded as text!")
            
            with col_download_pdf:
                if st.download_button(
                    label="Download PDF",
                    data=create_chat_pdf(),
                    file_name=f"chat_history_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf"
                ):
                    st.success("Chat history downloaded as PDF!")

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
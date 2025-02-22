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
from typing import Literal

# UI Translations
UI_TRANSLATIONS = {
    "English": {
        "title": "Disaster Management Chatbot",
        "sidebar_title": "Settings",
        "input_lang_label": "Input Language",
        "output_lang_label": "Output Language",
        "ui_lang_label": "Display Language",
        "chat_placeholder": "Type your message here...",
        "send_button": "Send",
        "clear_button": "Clear Chat",
        "download_title": "Download Chat History",
        "download_pdf": "Download as PDF",
        "download_text": "Download as Text",
        "success_pdf": "PDF downloaded successfully!",
        "success_text": "Text file downloaded successfully!",
        "error_pdf": "Could not generate PDF. Try text format instead.",
        "error_text": "Could not generate text file.",
        "chat_management": "Chat Management",
        "instructions": """### Instructions:
            - Ask questions about disaster management
            - Choose your preferred language for input and output
            - Get responses in your selected language
            - Use clear, simple language""",
    },
    "Sindhi": {
        "title": "آفت جي انتظام جو چيٽ بوٽ",
        "sidebar_title": "سيٽنگون",
        "input_lang_label": "ان پٽ ٻولي",
        "output_lang_label": "آؤٽ پٽ ٻولي",
        "ui_lang_label": "ڏيکاريندڙ ٻولي",
        "chat_placeholder": "پنهنجو سوال هتي لکو...",
        "send_button": "موڪلو",
        "clear_button": "چيٽ صاف ڪريو",
        "download_title": "چيٽ جي تاريخ ڊائونلوڊ ڪريو",
        "download_pdf": "PDF طور ڊائونلوڊ ڪريو",
        "download_text": "ٽيڪسٽ طور ڊائونلوڊ ڪريو",
        "success_pdf": "PDF ڊائونلوڊ ٿي وئي!",
        "success_text": "ٽيڪسٽ فائل ڊائونلوڊ ٿي وئي!",
        "error_pdf": "PDF نٿي ٺهي سگهي. ٽيڪسٽ فارميٽ استعمال ڪريو.",
        "error_text": "ٽيڪسٽ فائل نٿي ٺهي سگهي.",
        "chat_management": "چيٽ جو انتظام",
        "instructions": """### هدايتون:
            - آفتن جي انتظام بابت سوال پڇو
            - ان پٽ ۽ آؤٽ پٽ لاءِ پنهنجي پسند جي ٻولي چونڊيو
            - پنهنجي چونڊيل ٻولي ۾ جواب وٺو
            - صاف ۽ سادي ٻولي استعمال ڪريو""",
    }
}

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "input_language" not in st.session_state:
    st.session_state.input_language = "English"
if "output_language" not in st.session_state:
    st.session_state.output_language = "English"
if "ui_language" not in st.session_state:
    st.session_state.ui_language = "English"

def get_ui_text(key: str) -> str:
    """Get UI text in the selected language."""
    return UI_TRANSLATIONS[st.session_state.ui_language][key]

# Initialize session state for chat history and language preferences
if "messages" not in st.session_state:
    st.session_state.messages = []
if "input_language" not in st.session_state:
    st.session_state.input_language = "English"
if "output_language" not in st.session_state:
    st.session_state.output_language = "English"

def get_language_prompt(output_lang: Literal["English", "Sindhi"]) -> str:
    """Get the language-specific prompt instruction."""
    if output_lang == "Sindhi":
        return """سنڌي ۾ جواب ڏيو. مهرباني ڪري صاف ۽ سادي سنڌي استعمال ڪريو، اردو لفظن کان پاسو ڪريو. جواب تفصيلي ۽ سمجهه ۾ اچڻ جوڳو هجڻ گهرجي."""
    return "Respond in English using clear and professional language."

def create_chat_pdf():
    """Generate a PDF file of chat history with proper formatting."""
    try:
        # Create PDF object
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Add first page
        pdf.add_page()
        
        # Use default font for English
        pdf.set_font("Arial", "B", 16)
        
        # Add title
        pdf.cell(0, 10, "Disaster Management Chatbot - Conversation Log", ln=True, align='C')
        pdf.ln(10)
        
        # Add chat messages
        for message in st.session_state.messages:
            # Add role header
            role = "Bot" if message["role"] == "assistant" else "User"
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, f"{role}:", ln=True)
            
            # Add message content
            pdf.set_font("Arial", "", 11)
            text = message["content"]
            
            try:
                # Try to encode text to check for Unicode characters
                text.encode('latin-1')
            except UnicodeEncodeError:
                # If Unicode characters present, use a simpler representation
                text = f"[Message in {st.session_state.output_language}]"
            
            # Word wrap the text
            wrapped_text = textwrap.fill(text, width=85)
            for line in wrapped_text.split('\n'):
                pdf.multi_cell(0, 7, line)
            
            pdf.ln(5)
        
        # Return PDF as bytes
        return bytes(pdf.output())
        
    except Exception as e:
        st.error(f"Error generating PDF: {str(e)}")
        return None

def create_chat_text():
    """Generate a formatted text file of chat history."""
    try:
        output = []
        output.append("Disaster Management Chatbot - Conversation Log")
        output.append("=" * 50)
        output.append("")  # Empty line
        
        for message in st.session_state.messages:
            role = "Bot" if message["role"] == "assistant" else "User"
            output.append(f"{role}:")
            output.append(message['content'])
            output.append("-" * 30)
            output.append("")  # Empty line
        
        # Join with newlines and encode as UTF-8
        return "\n".join(output).encode('utf-8')
    except Exception as e:
        st.error(f"Error generating text file: {str(e)}")
        return None

def is_general_chat(query):
    """Check if the query is a general chat or greeting."""
    # Make patterns more specific to avoid false positives
    general_phrases = [
        '^hi$', '^hello$', '^hey$', 
        '^good morning$', '^good afternoon$', '^good evening$',
        '^how are you$', '^what\'s up$', '^nice to meet you$', 
        '^thanks$', '^thank you$', '^bye$', '^goodbye$', '^see you$',
        '^who are you$', '^what can you do$'
    ]
    
    query_lower = query.lower().strip()
    # Only match if these are standalone phrases
    return any(query_lower == phrase.strip('^$') for phrase in general_phrases)

def get_general_response(query):
    """Generate appropriate responses for general chat."""
    query_lower = query.lower()
    output_lang = st.session_state.output_language
    
    if output_lang == "Sindhi":
        if any(greeting in query_lower for greeting in ['hi', 'hello', 'hey']):
            return "السلام عليڪم! مان توهان جو آفتن جي انتظام جو مددگار آهيان. مان توهان جي ڪهڙي مدد ڪري سگهان ٿو؟"
        elif any(time in query_lower for time in ['good morning', 'good afternoon', 'good evening']):
            return "توهان جو مهرباني! مان توهان جي آفتن جي انتظام جي سوالن ۾ مدد ڪرڻ لاءِ حاضر آهيان."
        elif 'how are you' in query_lower:
            return "مان ٺيڪ آهيان، توهان جي پڇڻ جو مهرباني! مان آفتن جي انتظام جي معلومات ڏيڻ لاءِ تيار آهيان."
        elif 'thank' in query_lower:
            return "توهان جو مهرباني! آفتن جي انتظام بابت ڪو به سوال پڇڻ لاءِ آزاد محسوس ڪريو."
        elif 'bye' in query_lower or 'goodbye' in query_lower:
            return "خدا حافظ! جيڪڏهن توهان کي آفتن جي انتظام بابت وڌيڪ سوال هجن ته پوءِ ضرور پڇو."
        elif 'who are you' in query_lower:
            return "مان هڪ خاص آفتن جي انتظام جو مددگار آهيان. مان آفتن جي انتظام، حفاظتي اپاءَ ۽ آفتن جي جواب جي حڪمت عملي بابت معلومات ڏئي سگهان ٿو."
        else:
            return "مان آفتن جي انتظام جي معاملن ۾ ماهر آهيان. عام موضوعن تي مدد نه ڪري سگهندس، پر آفتن جي انتظام، ايمرجنسي طريقن يا حفاظتي اپاءَ بابت ڪو به سوال پڇڻ لاءِ آزاد محسوس ڪريو."
    else:
        # Original English responses
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
            retriever=vectorstore.as_retriever(search_kwargs={"k": 6}),
            return_source_documents=False,
            chain_type_kwargs={
                "prompt": PromptTemplate(
                    template=f"""You are a knowledgeable disaster management assistant. {get_language_prompt(st.session_state.output_language)}

Use the following guidelines to answer questions:

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

Context: {{context}}

Question: {{question}}

Response (remember to be natural and helpful):""",
                    input_variables=["context", "question"],
                )
            }
        )
        return qa_chain, llm
    except Exception as e:
        st.error(f"Error initializing RAG system: {str(e)}")
        st.stop()

def main():
    try:
        # Set page config
        st.set_page_config(page_title=get_ui_text("title"), layout="wide")
        
        # Sidebar
        with st.sidebar:
            st.title(get_ui_text("sidebar_title"))
            
            # Language settings
            st.session_state.input_language = st.selectbox(
                get_ui_text("input_lang_label"),
                ["English", "Sindhi"]
            )
            
            st.session_state.output_language = st.selectbox(
                get_ui_text("output_lang_label"),
                ["English", "Sindhi"]
            )
            
            st.session_state.ui_language = st.selectbox(
                get_ui_text("ui_lang_label"),
                ["English", "Sindhi"],
                key="ui_lang_selector"
            )
        
        # Main chat interface
        st.title(get_ui_text("title"))
        
        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Chat input
        if prompt := st.chat_input(get_ui_text("chat_placeholder")):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            with st.chat_message("assistant"):
                if is_general_chat(prompt):
                    response_text = get_general_response(prompt)
                else:
                    qa_chain, llm = initialize_rag()
                    response = qa_chain({"query": prompt})
                    response_text = response['result']
                st.markdown(response_text)
            st.session_state.messages.append({"role": "assistant", "content": response_text})
        
        # Instructions
        with st.sidebar:
            st.markdown(get_ui_text("instructions"))
        
        # Download options
        st.write(get_ui_text("download_title"))
        col_download_pdf, col_download_text = st.columns(2)
        
        with col_download_pdf:
            pdf_data = create_chat_pdf()
            if pdf_data is not None:
                if st.download_button(
                    get_ui_text("download_pdf"),
                    data=pdf_data,
                    file_name="chat_history.pdf",
                    mime="application/pdf"
                ):
                    st.success(get_ui_text("success_pdf"))
            else:
                st.error(get_ui_text("error_pdf"))
        
        with col_download_text:
            text_data = create_chat_text()
            if text_data is not None:
                if st.download_button(
                    get_ui_text("download_text"),
                    data=text_data,
                    file_name="chat_history.txt",
                    mime="text/plain"
                ):
                    st.success(get_ui_text("success_text"))
            else:
                st.error(get_ui_text("error_text"))
        
        # Chat management
        st.markdown(f"### {get_ui_text('chat_management')}")
        col_clear = st.columns(1)
        
        with col_clear[0]:
            if st.button(get_ui_text("clear_button")):
                st.session_state.messages = []
                st.rerun()
    
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
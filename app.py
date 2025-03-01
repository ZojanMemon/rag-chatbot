import streamlit as st
import google.generativeai as genai
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from datetime import datetime
from fpdf import FPDF
import textwrap
import io
import os
import pickle
from typing import Literal

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
        # Create PDF object with UTF-8 support
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        # Title
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "Disaster Management Chatbot - Conversation Log", 0, 1, 'C')
        pdf.ln(10)
        
        # Chat messages
        for message in st.session_state.messages:
            # Role header
            role = "Bot" if message["role"] == "assistant" else "User"
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, role + ":", 0, 1)
            
            # Message content
            pdf.set_font("Arial", "", 11)
            content = message["content"]
            
            # Handle Sindhi text
            try:
                # Try encoding as latin-1 first
                content.encode('latin-1')
                # If successful, write normally
                lines = textwrap.wrap(content, width=85)
                for line in lines:
                    pdf.cell(0, 7, line, 0, 1)
            except UnicodeEncodeError:
                # For Sindhi text, write "[Sindhi]" followed by transliterated version
                pdf.cell(0, 7, "[Sindhi Message]", 0, 1)
                # Try to write a transliterated version if possible
                try:
                    ascii_text = content.encode('ascii', 'replace').decode('ascii')
                    lines = textwrap.wrap(ascii_text, width=85)
                    for line in lines:
                        pdf.cell(0, 7, line, 0, 1)
                except:
                    pass
            
            pdf.ln(5)
        
        # Output PDF
        return pdf.output(dest='S').encode('latin-1', errors='replace')
        
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
        GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
        
        # Configure Google API
        genai.configure(api_key=GOOGLE_API_KEY)

        # Initialize embeddings
        try:
            embeddings = GoogleGenerativeAIEmbeddings(
                model="models/embedding-001",
                google_api_key=GOOGLE_API_KEY
            )
        except:
            # Fallback to HuggingFace embeddings if Google embeddings fail
            embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        
        # Create or load vector store
        index_file_path = "faiss_index"
        
        if os.path.exists(index_file_path):
            # Load existing index
            vectorstore = FAISS.load_local(index_file_path, embeddings)
        else:
            # Create a simple index with a few documents for testing
            texts = [
                "Disaster management involves preparing for, responding to, and recovering from disasters.",
                "Emergency protocols are standardized procedures to follow during emergencies.",
                "Safety measures are actions taken to prevent accidents and reduce risk.",
                "Risk assessment is the process of identifying potential hazards and evaluating their likelihood and impact.",
                "Relief operations involve providing aid to affected populations after a disaster."
            ]
            vectorstore = FAISS.from_texts(texts, embeddings)
            # Save the index
            vectorstore.save_local(index_file_path)
        
        # Create retriever
        retriever = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 5}
        )
        
        # Create prompt template
        template = """
        You are a helpful disaster management assistant that provides information about disaster management, 
        emergency protocols, safety measures, and relief operations.
        
        Use the following context to answer the question. If you don't know the answer, just say that you don't know.
        Don't try to make up an answer. Keep the answer concise and to the point.
        
        Context: {context}
        
        Question: {query}
        
        Answer:
        """
        
        # Create prompt
        prompt = PromptTemplate(
            template=template,
            input_variables=["context", "query"]
        )
        
        # Create language model
        llm = ChatGoogleGenerativeAI(
            model="gemini-pro",
            google_api_key=GOOGLE_API_KEY,
            temperature=0.3
        )
        
        # Create QA chain
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=False,
            chain_type_kwargs={"prompt": prompt}
        )
        
        return qa_chain, llm
        
    except Exception as e:
        st.error(f"Error initializing RAG system: {str(e)}")
        return None, None

def main():
    # Page config
    st.set_page_config(
        page_title="Disaster Management RAG Chatbot",
        page_icon="🤖",
        layout="wide"
    )

    # Custom CSS for layout
    st.markdown("""
        <style>
        /* Main container styling */
        .main {
            padding: 0;
            max-width: 1200px;
            margin: 0 auto;
        }
        
        /* Chat container */
        .chat-container {
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            padding-bottom: 100px;  /* Space for input box */
        }
        
        /* Fixed input container at bottom */
        .input-container {
            position: fixed;
            bottom: 0;
            left: 50%;
            transform: translateX(-50%);
            width: 800px;
            background-color: white;
            padding: 20px;
            border-top: 1px solid #ddd;
            z-index: 1000;
            display: none;
        }
        
        /* Sidebar styling */
        .css-1d391kg {
            padding: 20px;
        }
        
        /* Streamlit elements styling */
        div.stButton > button {
            width: 100%;
        }
        </style>
    """, unsafe_allow_html=True)
    
    try:
        # Initialize RAG system
        qa_chain, llm = initialize_rag()

        # Sidebar with settings and info
        with st.sidebar:
            st.title("Settings & Info")
            
            # Language Settings in an expander
            with st.expander("🌐 Language Settings", expanded=False):
                input_lang = st.selectbox(
                    "Select Input Language",
                    ["English", "Sindhi"],
                    key="input_language_selector",
                    index=0 if st.session_state.input_language == "English" else 1
                )
                output_lang = st.selectbox(
                    "Select Output Language",
                    ["English", "Sindhi"],
                    key="output_language_selector",
                    index=0 if st.session_state.output_language == "English" else 1
                )
                
                # Update session state if language changed
                if input_lang != st.session_state.input_language:
                    st.session_state.input_language = input_lang
                if output_lang != st.session_state.output_language:
                    st.session_state.output_language = output_lang
            
            # About section in an expander
            with st.expander("ℹ️ About", expanded=False):
                st.markdown("""
                ### Features
                This chatbot uses:
                - 🧠 Gemini Pro for text generation
                - 🔍 FAISS for vector storage
                - ⚡ LangChain for the RAG pipeline
                - 🌐 Multilingual support (English & Sindhi)
                
                ### Topics
                You can ask questions about:
                - 📋 Disaster management procedures
                - 🚨 Emergency protocols
                - 🛡️ Safety measures
                - 📊 Risk assessment
                - 🏥 Relief operations
                
                ### Tips
                - Be specific in your questions
                - Ask about one topic at a time
                - Use clear, simple language
                """)
            
            # Download options in an expander
            with st.expander("💾 Download Chat History", expanded=False):
                col_download_pdf, col_download_text = st.columns(2)
                
                with col_download_pdf:
                    if st.button("Generate PDF"):
                        st.session_state.pdf_data = create_chat_pdf()
                        st.success("PDF generated! Click download button below.")
                    
                    if "pdf_data" in st.session_state and st.session_state.pdf_data is not None:
                        if st.download_button(
                            "Download PDF",
                            data=st.session_state.pdf_data,
                            file_name="chat_history.pdf",
                            mime="application/pdf"
                        ):
                            st.success("PDF downloaded!")
                
                with col_download_text:
                    text_data = create_chat_text()
                    if text_data is not None:
                        if st.download_button(
                            "Download Text",
                            data=text_data,
                            file_name="chat_history.txt",
                            mime="text/plain"
                        ):
                            st.success("Text downloaded!")
            
            # Clear chat button at the bottom of sidebar
            if st.button("🗑️ Clear Chat History"):
                st.session_state.messages = []
                if "pdf_data" in st.session_state:
                    del st.session_state.pdf_data
                st.rerun()

        # Main chat interface
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        
        # Display chat title
        st.title("Disaster Management Assistant 🤖")
        
        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Fixed input box at bottom
        st.markdown('<div class="input-container">', unsafe_allow_html=True)
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
            st.session_state.messages.append({"role": "assistant", "content": response_text})
            
            # Update PDF data after new message
            if "pdf_data" in st.session_state:
                st.session_state.pdf_data = create_chat_pdf()
                
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
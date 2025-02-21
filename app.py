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
    pdf = FPDF()
    # Add a Unicode font that supports Sindhi
    pdf.add_font('NotoSans', '', 'NotoSans-Regular.ttf', uni=True)
    pdf.add_page()
    
    # Set up the PDF
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font('NotoSans', '', 16)
    pdf.cell(0, 10, "Disaster Management Chatbot - Conversation Log", ln=True, align='C')
    pdf.ln(10)
    
    # Add content
    pdf.set_font('NotoSans', '', 12)
    for message in st.session_state.messages:
        # Role header
        pdf.set_font('NotoSans', '', 12)
        role = "Bot" if message["role"] == "assistant" else "User"
        pdf.cell(0, 10, f"{role}:", ln=True)
        
        # Message content with proper wrapping
        pdf.set_font('NotoSans', '', 11)
        text = message["content"]
        wrapped_text = textwrap.fill(text, width=85)
        for line in wrapped_text.split('\n'):
            pdf.cell(0, 7, line, ln=True)
        pdf.ln(5)
    
    # Use bytes IO to handle Unicode
    return pdf.output().encode('latin-1')

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
            model="gemini-pro",
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
                st.session_state.messages.append({"role": "assistant", "content": response_text})

        # Sidebar with information
        with col2:
            st.title("Settings")
            
            # Language selection
            st.markdown("### Language Settings")
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
                st.rerun()
            if output_lang != st.session_state.output_language:
                st.session_state.output_language = output_lang
                st.rerun()

            st.title("About")
            st.markdown("""
            ### Features
            This chatbot uses:
            - 🧠 Gemini Pro for text generation
            - 🔍 Pinecone for vector storage
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
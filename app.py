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

# UI translations
UI_TRANSLATIONS = {
    "English": {
        "title": "Disaster Management RAG Chatbot 🤖",
        "description": "This chatbot can answer questions about disaster management based on the provided documentation.",
        "input_placeholder": "Ask your question here",
        "clear_chat": "Clear Chat",
        "download_text": "Download Text",
        "download_pdf": "Download PDF",
        "about_title": "About",
        "features_title": "Features",
        "topics_title": "Topics",
        "tips_title": "Tips",
        "chat_management": "Chat Management",
        "success_text": "Chat history downloaded as text!",
        "success_pdf": "Chat history downloaded as PDF!",
    },
    "سنڌي": {  # Sindhi
        "title": "آفت جي انتظام RAG چيٽ بوٽ 🤖",
        "description": "هي چيٽ بوٽ فراهم ڪيل دستاويزن جي بنياد تي آفت جي انتظام بابت سوالن جا جواب ڏئي سگھي ٿو.",
        "input_placeholder": "پنهنجو سوال هتي پڇو",
        "clear_chat": "چيٽ صاف ڪريو",
        "download_text": "ٽيڪسٽ ڊائونلوڊ ڪريو",
        "download_pdf": "PDF ڊائونلوڊ ڪريو",
        "about_title": "تعارف",
        "features_title": "خاصيتون",
        "topics_title": "موضوع",
        "tips_title": "صلاح",
        "chat_management": "چيٽ جو انتظام",
        "success_text": "چيٽ جي تاريخ ٽيڪسٽ طور ڊائونلوڊ ٿي وئي!",
        "success_pdf": "چيٽ جي تاريخ PDF طور ڊائونلوڊ ٿي وئي!",
    }
}

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "language" not in st.session_state:
    st.session_state.language = "English"

def get_translation(key):
    """Get translated text based on current language."""
    return UI_TRANSLATIONS[st.session_state.language][key]

def create_chat_pdf():
    """Generate a PDF file of chat history with proper formatting."""
    pdf = FPDF()
    pdf.add_page()
    
    # Set up the PDF with Unicode support for Sindhi
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_font('NotoNastaliqUrdu', '', 'NotoNastaliqUrdu-Regular.ttf', uni=True)
    
    # Use appropriate font based on language
    if st.session_state.language == "سنڌي":
        pdf.set_font('NotoNastaliqUrdu', '', 16)
    else:
        pdf.set_font('Arial', 'B', 16)
    
    pdf.cell(0, 10, get_translation("title"), ln=True, align='C')
    pdf.ln(10)
    
    for message in st.session_state.messages:
        if st.session_state.language == "سنڌي":
            pdf.set_font('NotoNastaliqUrdu', '', 12)
        else:
            pdf.set_font('Arial', 'B', 12)
        
        role = "Bot" if message["role"] == "assistant" else "User"
        pdf.cell(0, 10, f"{role}:", ln=True)
        
        if st.session_state.language == "سنڌي":
            pdf.set_font('NotoNastaliqUrdu', '', 11)
        else:
            pdf.set_font('Arial', '', 11)
        
        text = message["content"]
        wrapped_text = textwrap.fill(text, width=85)
        for line in wrapped_text.split('\n'):
            pdf.cell(0, 7, line, ln=True)
        pdf.ln(5)
    
    return pdf.output(dest='S').encode('latin1')

def create_chat_text():
    """Generate a formatted text file of chat history."""
    output = io.StringIO()
    output.write(f"{get_translation('title')}\n")
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
    general_phrases_en = [
        'hi ', 'hello ', 'hey ', 'good morning', 'good afternoon', 'good evening',
        'how are you', 'what\'s up', 'nice to meet you', 'thanks', 'thank you',
        'bye', 'goodbye', 'see you', 'who are you', 'what can you do'
    ]
    
    general_phrases_sd = [
        'سلام', 'السلام عليڪم', 'هيلو', 'صبح بخير',
        'ڪيئن آهيو', 'مهرباني', 'شڪريو',
        'خدا حافظ', 'توهان ڪير آهيو', 'توهان ڇا ڪري سگھو ٿا'
    ]
    
    query = f" {query.lower()} "
    return any(f" {phrase} " in query for phrase in general_phrases_en + general_phrases_sd)

def get_general_response(query):
    """Generate appropriate responses for general chat in the selected language."""
    query_lower = query.lower()
    
    if st.session_state.language == "سنڌي":
        if any(greeting in query_lower for greeting in ['سلام', 'هيلو', 'السلام عليڪم']):
            return "وعليڪم السلام! مان توهان جو آفت جي انتظام جو مددگار آهيان. مان توهان جي ڪيئن مدد ڪري سگھان ٿو؟"
        elif 'ڪيئن آهيو' in query_lower:
            return "مان ٺيڪ آهيان، توهان جي پڇڻ جو شڪريو! مان آفت جي انتظام جي معلومات ۾ توهان جي مدد ڪرڻ لاءِ تيار آهيان."
        elif 'شڪريو' in query_lower or 'مهرباني' in query_lower:
            return "توهان جو مهرباني! آفت جي انتظام بابت ڪو به سوال هجي ته ضرور پڇو."
        elif 'خدا حافظ' in query_lower:
            return "خدا حافظ! جيڪڏهن آفت جي انتظام بابت وڌيڪ سوال هجن ته پوءِ ملندا سين."
        elif 'توهان ڪير آهيو' in query_lower:
            return "مان هڪ خاص آفت جي انتظام جو چيٽ بوٽ آهيان. مان آفت جي انتظام، هنگامي حالتن ۽ حفاظتي اپاين بابت معلومات ڏئي سگھان ٿو."
        elif 'توهان ڇا ڪري سگھو ٿا' in query_lower:
            return """مان توهان جي مدد ڪري سگھان ٿو:
- هنگامي حالتن ۾ ڪارروائي
- آفت جي تياري
- حفاظتي اپاءَ
- خطري جو جائزو
- امدادي ڪارروائيون
- ۽ ٻيون گھڻيون ڳالهيون

ڪنهن به موضوع تي سوال پڇي سگھو ٿا!"""
        else:
            return "مان آفت جي انتظام جو ماهر آهيان. عام موضوعن تي مدد نٿو ڪري سگھان، پر آفت جي انتظام، هنگامي حالتن ۽ حفاظتي اپاين بابت سوالن جا جواب ضرور ڏيندس."
    else:
        if any(greeting in query_lower for greeting in ['hi', 'hello', 'hey']):
            return "Hello! I'm your disaster management assistant. How can I help you today?"
        elif any(time in query_lower for greeting in ['good morning', 'good afternoon', 'good evening']):
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

        # Initialize cross-lingual embeddings
        embeddings = HuggingFaceEmbeddings(
            model_name='sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
            model_kwargs={'device': 'cpu'},
            encode_kwargs={
                'normalize_embeddings': True,
                'batch_size': 32
            }
        )

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

        # Create the QA chain with multilingual prompt
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vectorstore.as_retriever(search_kwargs={"k": 4}),
            return_source_documents=False,
            chain_type_kwargs={
                "prompt": PromptTemplate(
                    template="""You are a multilingual disaster management assistant that can communicate in both English and Sindhi. Detect the language of the user's question and respond in the same language. Follow these guidelines:

1. If the context contains relevant information:
   - Provide a detailed and comprehensive answer using the information
   - Include specific details and procedures from the source
   - Structure the response in a clear, readable format
   - Use professional and precise language in the user's preferred language

2. If the context does NOT contain sufficient information:
   - Provide a general, informative response based on common disaster management principles
   - Be honest about not having specific details
   - Offer to help with related topics that are within your knowledge base
   - Never make up specific numbers or procedures
   - Guide the user towards asking more specific questions about disaster management
   - Maintain the same language as the user's question

Context: {context}

Question: {question}

Response (in the same language as the question):""",
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
    
    # Language selector in sidebar
    st.sidebar.title("Language Settings / ٻولي جون ترتيبون")
    selected_language = st.sidebar.selectbox(
        "Choose Language / زبان چونڊيو",
        ["English", "سنڌي"],
        index=0 if st.session_state.language == "English" else 1
    )
    
    if selected_language != st.session_state.language:
        st.session_state.language = selected_language
        st.rerun()
    
    # Header
    st.title(get_translation("title"))
    st.markdown(get_translation("description"))

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
            if prompt := st.chat_input(get_translation("input_placeholder")):
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
            st.title(get_translation("about_title"))
            if st.session_state.language == "English":
                st.markdown("""
                ### Features
                This chatbot uses:
                - 🧠 Gemini Pro for text generation
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
                - Be specific in your questions
                - Ask about one topic at a time
                - Use clear, simple language
                """)
            else:
                st.markdown("""
                ### خاصيتون
                هي چيٽ بوٽ استعمال ڪري ٿو:
                - 🧠 جيميني پرو ٽيڪسٽ ٺاهڻ لاءِ
                - 🔍 پائن ڪون ڊيٽا ذخيرو ڪرڻ لاءِ
                - ⚡ لينگ چين RAG پائپ لائين لاءِ
                
                ### موضوع
                توهان هنن موضوعن تي سوال پڇي سگھو ٿا:
                - 📋 آفت جي انتظام جا طريقا
                - 🚨 هنگامي حالتن جا اصول
                - 🛡️ حفاظتي اپاءَ
                - 📊 خطري جو جائزو
                - 🏥 امدادي ڪارروائيون
                
                ### صلاح
                - پنهنجي سوالن ۾ خاص ڳالهه پڇو
                - هڪ وقت تي هڪ موضوع تي سوال پڇو
                - سادي ۽ صاف ٻولي استعمال ڪريو
                """)

            # Add buttons for chat management
            st.markdown(f"### {get_translation('chat_management')}")
            col_clear, col_download_text, col_download_pdf = st.columns(3)
            
            with col_clear:
                if st.button(get_translation("clear_chat")):
                    st.session_state.messages = []
                    st.rerun()
            
            with col_download_text:
                if st.download_button(
                    label=get_translation("download_text"),
                    data=create_chat_text(),
                    file_name=f"chat_history_{datetime.now().strftime('%Y%m%d')}.txt",
                    mime="text/plain"
                ):
                    st.success(get_translation("success_text"))
            
            with col_download_pdf:
                if st.download_button(
                    label=get_translation("download_pdf"),
                    data=create_chat_pdf(),
                    file_name=f"chat_history_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf"
                ):
                    st.success(get_translation("success_pdf"))

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
import google.generativeai as genai
from langchain_core.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone as PineconeClient
import pandas as pd
from datetime import datetime
import csv
import io

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Add timestamp to messages
if "messages_with_time" not in st.session_state:
    st.session_state.messages_with_time = []

def download_chat_history():
    """Generate a CSV file of chat history."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Timestamp', 'Role', 'Message'])
    for msg in st.session_state.messages_with_time:
        writer.writerow([msg['timestamp'], msg['role'], msg['content']])
    csv_data = output.getvalue()
    output.close()
    return csv_data

def is_general_chat(query):
    """Check if the query is a general chat or greeting."""
    general_phrases = [
        'hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening',
        'how are you', 'what\'s up', 'nice to meet you', 'thanks', 'thank you',
        'bye', 'goodbye', 'see you', 'who are you', 'what can you do'
    ]
    return any(phrase in query.lower() for phrase in general_phrases)

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

        # Initialize embeddings with CPU and additional parameters
        try:
            embeddings = HuggingFaceEmbeddings(
                model_name='all-MiniLM-L6-v2',
                model_kwargs={
                    'device': 'cpu'
                },
                encode_kwargs={
                    'normalize_embeddings': True,
                    'batch_size': 32
                }
            )
        except Exception as e:
            st.error(f"Error initializing embeddings: {str(e)}")
            st.stop()

        # Initialize vector store with new class
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

        # Create the QA chain with original prompt
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vectorstore.as_retriever(search_kwargs={"k": 4}),
            return_source_documents=False,
            chain_type_kwargs={
                "prompt": PromptTemplate(
                    template="""You are a detailed and thorough assistant. For this question, you must follow these rules:
1. Provide a complete and detailed answer using ALL information from the context
2. Do not summarize or shorten any details
3. Include every relevant fact and description from the source text
4. Use the same detailed language as the original document
5. Structure the answer in a clear, readable format

Context: {context}

Question: {question}

Provide a comprehensive answer that includes every detail from the context:""",
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
                # Get current timestamp
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Display user message
                with st.chat_message("user"):
                    st.markdown(prompt)
                st.session_state.messages.append({"role": "user", "content": prompt})
                st.session_state.messages_with_time.append({
                    "timestamp": current_time,
                    "role": "user",
                    "content": prompt
                })

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
                st.session_state.messages_with_time.append({
                    "timestamp": current_time,
                    "role": "assistant",
                    "content": response_text
                })

        # Sidebar with information
        with col2:
            st.title("About")
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

            # Add buttons for chat management
            col_clear, col_download = st.columns(2)
            
            with col_clear:
                if st.button("Clear Chat"):
                    st.session_state.messages = []
                    st.session_state.messages_with_time = []
                    st.rerun()
            
            with col_download:
                if st.download_button(
                    label="Download Chat",
                    data=download_chat_history(),
                    file_name=f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                ):
                    st.success("Chat history downloaded successfully!")

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
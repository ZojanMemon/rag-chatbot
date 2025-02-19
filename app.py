import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
import google.generativeai as genai
from langchain_core.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone as PineconeClient

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

def is_general_question(question):
    general_patterns = [
        "hi", "hello", "hey", "how are you", "help", "what can you do",
        "who are you", "what is this", "good morning", "good afternoon",
        "good evening", "thanks", "thank you"
    ]
    return any(pattern in question.lower() for pattern in general_patterns)

def get_general_response(question):
    responses = {
        "greeting": """Hello! I am a Disaster Management chatbot. I can help you with:
- Disaster management procedures
- Emergency protocols
- Safety measures
- Risk assessment
- Relief operations

Please ask specific questions about disaster management, and I'll provide detailed information from my knowledge base.""",
        
        "help": """I can assist you with disaster management related questions such as:
- "What are the key steps in emergency evacuation?"
- "How to prepare for natural disasters?"
- "What are the best practices for disaster response?"
- "What safety measures should be taken during a specific disaster?"

Please ask your question, and I'll provide detailed information from authentic disaster management sources."""
    }

    if any(word in question.lower() for word in ["hi", "hello", "hey", "good"]):
        return responses["greeting"]
    return responses["help"]

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

        # Create the QA chain with updated prompt
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vectorstore.as_retriever(search_kwargs={"k": 4}),
            return_source_documents=False,
            chain_type_kwargs={
                "prompt": PromptTemplate(
                    template="""You are a specialized Disaster Management Assistant. Use the following rules:

1. If the context contains relevant information:
   - Provide a complete and detailed answer using ALL information from the context
   - Include every relevant fact and description
   - Use clear, professional language
   - Structure the answer in a readable format

2. If the context doesn't contain relevant information:
   - Politely inform that the question is outside the scope of available information
   - Suggest asking questions about disaster management, emergency procedures, or safety measures

Context: {context}

Question: {question}

Response:""",
                    input_variables=["context", "question"],
                )
            }
        )
        return qa_chain
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
        qa_chain = initialize_rag()

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
                        if is_general_question(prompt):
                            response = get_general_response(prompt)
                        else:
                            qa_response = qa_chain({"query": prompt})
                            response = qa_response['result']
                            
                            # Check if response seems irrelevant
                            if any(phrase in response.lower() for phrase in ["context provided includes", "based on the context provided"]):
                                response = """I apologize, but I don't have specific information to answer that question. Please ask questions related to:
- Disaster management procedures
- Emergency protocols
- Safety measures
- Risk assessment
- Relief operations

This will help me provide accurate and helpful information from my knowledge base."""
                            
                        st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

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

            # Add a clear chat button
            if st.button("Clear Chat History"):
                st.session_state.messages = []
                st.rerun()

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
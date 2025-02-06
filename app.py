import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
import google.generativeai as genai
from langchain_core.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore  # Updated import
from pinecone import Pinecone as PineconeClient

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

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

        # Initialize embeddings with CPU
        embeddings = HuggingFaceEmbeddings(
            model_name='all-MiniLM-L6-v2',
            model_kwargs={'device': 'cpu'}  # Force CPU usage
        )

        # Initialize vector store with new class
        index_name = "pdfinfo"
        vectorstore = PineconeVectorStore(
            client=pc,
            index_name=index_name,
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

        # Create the QA chain
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
        return qa_chain
    except Exception as e:
        st.error(f"Error initializing RAG system: {str(e)}")
        st.stop()

def main():
    # Page config
    st.set_page_config(page_title="Disaster Management RAG Chatbot", page_icon="🤖")
    
    # Header
    st.title("Disaster Management RAG Chatbot 🤖")
    st.markdown("""
    This chatbot can answer questions about disaster management based on the provided documentation.
    """)

    try:
        # Initialize RAG system
        qa_chain = initialize_rag()

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
                    response = qa_chain({"query": prompt})
                    st.markdown(response['result'])
            st.session_state.messages.append({"role": "assistant", "content": response['result']})

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

    # Sidebar with information
    with st.sidebar:
        st.title("About")
        st.markdown("""
        This chatbot uses:
        - Gemini Pro for text generation
        - Pinecone for vector storage
        - LangChain for the RAG pipeline
        
        You can ask questions about:
        - Disaster management procedures
        - Emergency protocols
        - Safety measures
        - And more!
        """)

if __name__ == "__main__":
    main()
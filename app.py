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

def is_meaningful_context(context):
    # Check if context contains actual content (not just numbers)
    meaningful_words = [word for word in context.split() if not word.isdigit()]
    return len(meaningful_words) > 5

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

        # Create a retriever with debug info
        retriever = vectorstore.as_retriever(
            search_kwargs={
                "k": 4  # Number of documents to retrieve
            }
        )

        # Create the QA chain
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True,
            chain_type_kwargs={
                "prompt": PromptTemplate(
                    template="""You are a knowledgeable assistant specializing in disaster management. You have access to specific documentation about disaster management procedures and protocols.

If the provided context contains ANY relevant information about disaster management (even if partial), use that information to construct a helpful response. Only respond with an apology if the context is completely irrelevant or empty.

Here's how you should process the response:

1. If the context contains ANY relevant disaster management information:
   - Extract and present all relevant information
   - Structure your response clearly
   - Use bullet points or sections if appropriate
   - Include specific details from the context
   - If the information is partial, still provide what's available

2. ONLY if the context is completely irrelevant or contains no disaster management information:
   Respond with: "I apologize, but I don't have enough information in my knowledge base to answer this question. I can only provide information about disaster management topics that are contained in my documentation."

Context: {context}

Question: {question}

Provide a detailed response based on the context above:""",
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
                        response = qa_chain({"query": prompt})
                        
                        # Debug information in sidebar
                        with col2:
                            with st.expander("Debug Info"):
                                st.write("Retrieved Documents:")
                                if 'source_documents' in response:
                                    for i, doc in enumerate(response['source_documents']):
                                        st.write(f"Document {i+1}:")
                                        st.write(doc.page_content[:200] + "...")
                                        # Check if context is meaningful
                                        if not is_meaningful_context(doc.page_content):
                                            st.write("⚠️ This document may not contain meaningful content")
                                else:
                                    st.write("No documents retrieved")
                        
                        st.markdown(response['result'])
                st.session_state.messages.append({"role": "assistant", "content": response['result']})

        # Information sidebar
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
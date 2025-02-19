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
    # Expanded list of patterns to catch more variations
    general_patterns = {
        'greeting': [
            "hi", "hello", "hey", "greetings", "good morning", "good afternoon", 
            "good evening", "how are you", "what's up", "howdy"
        ],
        'about_bot': [
            "who are you", "what are you", "what can you do", "what do you do",
            "help me", "how can you help", "what is this", "tell me about yourself",
            "your purpose", "your capabilities", "what should i ask"
        ],
        'gratitude': [
            "thanks", "thank you", "appreciate", "grateful", "helpful"
        ],
        'general_chat': [
            "how's it going", "nice to meet you", "pleasure", "bye", "goodbye",
            "see you", "talk to you later"
        ]
    }
    
    # Convert question to lowercase for matching
    question_lower = question.lower()
    
    # Check each category of patterns
    for category, patterns in general_patterns.items():
        if any(pattern in question_lower for pattern in patterns):
            return True, category
            
    # Check for question words without context
    question_words = ["what", "how", "can", "could", "would", "will", "should"]
    if any(word in question_lower.split() for word in question_words):
        # Look for disaster-related keywords
        disaster_keywords = ["disaster", "emergency", "crisis", "safety", "protocol", 
                           "procedure", "management", "risk", "hazard", "evacuation",
                           "response", "relief", "rescue", "preparation", "plan"]
        # If it's a question but doesn't contain disaster-related keywords
        if not any(keyword in question_lower for keyword in disaster_keywords):
            return True, "general_question"
            
    return False, None

def get_general_response(category):
    responses = {
        'greeting': """Hello! I'm your Disaster Management Assistant. I'm here to help you with:
- Disaster management procedures and protocols
- Emergency response strategies
- Safety measures and risk assessment
- Relief operations and evacuation plans

How can I assist you today?""",

        'about_bot': """I am a specialized Disaster Management Assistant that can help you with:
- Detailed information about disaster management procedures
- Emergency protocols and response strategies
- Safety measures and preventive actions
- Risk assessment and mitigation
- Relief operation planning and execution

You can ask me specific questions like:
1. "What are the key steps in emergency evacuation?"
2. "How should we prepare for natural disasters?"
3. "What are the best practices for disaster response?"
4. "What safety measures should be taken during [specific disaster]?"
5. "How to create an effective disaster management plan?"

Feel free to ask any disaster management related question!""",

        'gratitude': """You're welcome! If you have any more questions about disaster management, emergency procedures, or safety measures, feel free to ask.""",

        'general_chat': """I'm focused on providing information about disaster management. Please feel free to ask any specific questions about emergency procedures, safety measures, or disaster response strategies.""",

        'general_question': """I'm a specialized Disaster Management Assistant. To help you better, could you please:
1. Ask specific questions about disaster management
2. Include keywords related to emergencies, safety, or procedures
3. Mention the specific aspect of disaster management you're interested in

For example:
- "What are the emergency evacuation procedures?"
- "How to prepare for natural disasters?"
- "What safety measures are important during a crisis?"
"""
    }
    
    return responses.get(category, responses['about_bot'])

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
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True, 'batch_size': 32}
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
                    template="""You are a specialized Disaster Management Assistant with access to a comprehensive knowledge base. Follow these instructions carefully:

1. ALWAYS try to answer from the provided context first:
   - If the context contains ANY relevant information, use it to provide an answer
   - Even if the context only partially answers the question, provide that information
   - Combine and structure information from different parts of the context if available

2. When using the context:
   - Include specific details and examples from the context
   - Use professional and clear language
   - Structure the answer in a readable format

3. Only if the context has absolutely NO relevant information:
   - Clearly state that the specific information is not in your current knowledge base
   - Suggest related topics that are available in your knowledge base
   - Guide the user to rephrase their question if needed

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
                        is_general, category = is_general_question(prompt)
                        
                        if is_general:
                            response = get_general_response(category)
                        else:
                            qa_response = qa_chain({"query": prompt})
                            response = qa_response['result']
                            
                            # Enhanced irrelevant response detection
                            irrelevant_patterns = [
                                "context provided includes the numbers",
                                "based on the numbers in the context",
                                "cannot provide specific information about",
                                "i cannot provide specific details about",
                                "i cannot provide information about",
                                "i don't have access to specific information"
                            ]
                            
                            if any(pattern in response.lower() for pattern in irrelevant_patterns):
                                # Try to get a more focused response
                                focused_prompt = f"Using the available disaster management documentation, what information can you provide about {prompt}? If the specific details are not available, what related information do we have?"
                                qa_response = qa_chain({"query": focused_prompt})
                                response = qa_response['result']
                                
                                # If still no relevant information
                                if any(pattern in response.lower() for pattern in irrelevant_patterns):
                                    response = """While I don't have the exact information you're looking for, I can help you find related information in our disaster management knowledge base. 

To get the most relevant information:
1. Try focusing on specific aspects like:
   - Specific disaster types or scenarios
   - Particular phases of disaster management
   - Concrete procedures or protocols

2. You can also rephrase your question to focus on:
   - Available emergency procedures
   - Documented safety protocols
   - Standard operating procedures
   - Risk assessment methods

Would you like to know about any of these related topics?"""
                        
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
# -*- coding: utf-8 -*- # Add this line for better UTF-8 handling, especially for comments/strings

import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
import google.generativeai as genai
from langchain_core.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
# from langchain_community.vectorstores import FAISS # Not used if using Pinecone
from datetime import datetime
from fpdf import FPDF
import io
import textwrap
from typing import Literal
# Assuming these components exist in your project structure
from components.email_ui import show_email_ui
from auth.authenticator import FirebaseAuthenticator
from auth.chat_history import ChatHistoryManager
from auth.ui import auth_page, user_sidebar, chat_history_sidebar, sync_chat_message, load_user_preferences, save_user_preferences
from services.email_service import EmailService

# --- Constants and Configuration ---

# Emergency authority email mapping (Example - replace with actual emails)
EMERGENCY_AUTHORITIES = {
    "Flood": "flood.authority@example.com",
    "Earthquake": "earthquake.response@example.com",
    "Fire": "fire.department@example.com",
    "Medical": "medical.emergency@example.com",
    "General": "general.emergency@example.com"
}

# --- Session State Initialization ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "input_language" not in st.session_state:
    st.session_state.input_language = "English"
if "output_language" not in st.session_state:
    st.session_state.output_language = "English"
if "show_settings" not in st.session_state:
    st.session_state.show_settings = False
if "thinking" not in st.session_state:
    st.session_state.thinking = False
if "current_session_id" not in st.session_state:
    # Initialize with a default or fetch the latest session ID upon login
    st.session_state.current_session_id = None

# --- Helper Functions ---

def get_language_prompt(output_lang: Literal["English", "Sindhi", "Urdu"]) -> str:
    """Get the language-specific prompt instruction."""
    if output_lang == "Sindhi":
        return """سنڌي ۾ جواب ڏيو. مهرباني ڪري صاف ۽ سادي سنڌي استعمال ڪريو، اردو لفظن کان پاسو ڪريو. جواب تفصيلي ۽ سمجهه ۾ اچڻ جوڳو هجڻ گهرجي."""
    elif output_lang == "Urdu":
        return """اردو میں جواب دیں۔ براہ کرم واضح اور سادہ اردو استعمال کریں۔ جواب تفصیلی اور سمجھنے کے قابل ہونا چاہیے۔"""
    return "Respond in English using clear and professional language."

def create_chat_pdf():
    """Generate a PDF file of chat history."""
    # NOTE: FPDF has limitations with complex scripts like Sindhi/Urdu.
    # Consider using libraries like reportlab for better multilingual PDF support if needed.
    try:
        pdf = FPDF()
        pdf.add_page()
        # Add a font that supports the characters or use a fallback mechanism
        # This is a basic implementation; proper font handling is complex.
        try:
            # Try adding a commonly available font that might support some characters
            pdf.add_font('Arial', '', 'arial.ttf', uni=True)
            pdf.set_font('Arial', '', 11)
        except RuntimeError:
            # Fallback to default font if Arial isn't found/doesn't work
            st.warning("Arial font not found for PDF generation. Using default font, some characters might not render correctly.")
            pdf.set_font('helvetica', '', 11) # Use 'helvetica' or 'times'

        # Title
        pdf.set_font_size(16)
        # Manually encode title to handle potential issues if default font doesn't support all chars
        try:
            title = "Disaster Management Chatbot - Conversation Log".encode('latin-1', 'replace').decode('latin-1')
            pdf.cell(0, 10, title, 0, 1, 'C')
        except Exception:
             pdf.cell(0, 10, "Chatbot Conversation Log", 0, 1, 'C') # Fallback title
        pdf.ln(10)

        pdf.set_font_size(11) # Reset font size for content

        for message in st.session_state.messages:
            role = "Bot" if message["role"] == "assistant" else "User"
            try:
                role_text = f"{role}:".encode('latin-1', 'replace').decode('latin-1')
                pdf.set_font(style='B') # Bold for role
                pdf.multi_cell(0, 7, role_text)
                pdf.set_font(style='') # Regular for content

                # Attempt to encode content safely for PDF
                content_text = message["content"].encode('latin-1', 'replace').decode('latin-1')
                pdf.multi_cell(0, 7, content_text)
                pdf.ln(3) # Small space between messages
            except Exception as pdf_err:
                 st.error(f"Skipping message due to PDF encoding error: {pdf_err}")
                 pdf.multi_cell(0, 7, f"[{role} - Error rendering message content]")
                 pdf.ln(3)

        # Output PDF safely encoded
        return pdf.output(dest='S').encode('latin-1')

    except Exception as e:
        st.error(f"Error generating PDF: {str(e)}")
        return None

def create_chat_text():
    """Generate a formatted text file of chat history."""
    try:
        output = []
        output.append("Disaster Management Chatbot - Conversation Log")
        output.append("=" * 50)
        output.append("")

        for message in st.session_state.messages:
            role = "Bot" if message["role"] == "assistant" else "User"
            output.append(f"{role}:")
            # Directly use the UTF-8 content
            output.append(message['content'])
            output.append("-" * 30)
            output.append("")

        # Join with newlines and encode as UTF-8
        return "\n".join(output).encode('utf-8')
    except Exception as e:
        st.error(f"Error generating text file: {str(e)}")
        return None

def should_use_general_response(query):
    """
    Check if the query should be handled by the general response function.
    This includes simple greetings/phrases AND specific keywords for fixed answers.
    Returns True if get_general_response should be used, False otherwise.
    """
    query_lower = query.lower().strip() # Normalize query

    # 1. Check for exact simple phrases (like original is_general_chat)
    simple_phrases = [
        'hi', 'hello', 'hey',
        'good morning', 'good afternoon', 'good evening',
        'how are you', "what's up", 'nice to meet you',
        'thanks', 'thank you',
        'bye', 'goodbye', 'see you',
        'who are you', 'what can you do', 'what is your name'
    ]
    # Check for exact matches first for simple greetings/phrases
    if query_lower in simple_phrases:
        return True

    # Ensure session state has the language
    if 'output_language' not in st.session_state:
        st.session_state.output_language = "English"
    output_lang = st.session_state.output_language

    # 2. Check for keywords based on the selected language
    keywords_to_check = []
    if output_lang == "Sindhi":
        keywords_to_check = [
            "زلزلي", "زلزلو", "لوڏا", "زمين تي ڪريو", "پناهه",
            "گرمي جي لهر", "سخت گرمي", "محفوظ", "هائيڊريٽ", "پاڻي", "سج",
            "ٻيلهه جي باهه", "باهه ويجهو", "باهه", "نڪتو", "ڀڄڻ",
            "سامونڊي طوفان", "طوفان", "تياري",
            "ايمرجنسي کٽ", "سامان", "ڇا رکڻ",
            "گهر بچائڻ", "ٻوڏ", "ٻوڏ کان بچاء",
            "نيڪالي", "نڪرڻ", "ٻاهر وڃڻ", "ايمرجنسي قدم",
            "ڄاڻ رکڻ", "آفت جي خبرون", "خبرون", "الرٽس", "معلومات",
            "مقامي اختيارين", "اختيارين رابطو", "سرڪاري نمبر", "حڪام",
            "ايمرجنسي نمبر", "ايمرجنسي رابطو", "مدد نمبر", "1736",
            "ريسڪيو ٽيم", "ريسڪيو", "بچاء ٽيم", "مدد ٽيم",
            "پيئڻ جو پاڻي", "صاف پاڻي", "پاڻي محفوظ", "پاڻي پيئڻ",
            "طبي مدد", "ڊاڪٽر", "ڪلينڪ", "اسپتال", "پهرين مدد", "زخمي", "بيمار",
            "خاندان رابطو", "خاندان ملائڻ", "رشتيدار", "فون", "گهر ڳالهايو"
        ]
    elif output_lang == "Urdu":
        keywords_to_check = [
            "زلزلے", "زلزلہ", "جھٹکے", "گر جائیں", "پناہ",
            "گرمی کی لہر", "شدید گرمی", "محفوظ", "ہائیڈریٹ", "پانی", "دھوپ",
            "جنگل کی آگ", "آگ قریب", "آگ", "نکلو", "بھاگنا",
            "سمندری طوفان", "طوفان", "تیاری",
            "ایمرجنسی کٹ", "سامان", "کیا رکھنا",
            "گھر بچانا", "سیلاب", "سیلاب سے بچاؤ",
            "نکاسی", "نکلنا", "باہر جانا", "ایمرجنسی اقدامات",
            "مطلع رہنا", "آفت کی خبریں", "خبریں", "الرٹس", "معلومات",
            "مقامی حکام", "حکام رابطہ", "سرکاری نمبر", "حکومت",
            "ایمرجنسی نمبر", "ایمرجنسی رابطہ", "مدد نمبر", "1736",
            "ریسکیو ٹیم", "ریسکیو", "بچاؤ ٹیم", "مدد ٹیم",
            "پینے کا پانی", "صاف پانی", "پانی محفوظ", "پانی پینا",
            "طبی مدد", "ڈاکٹر", "کلینک", "ہسپتال", "ابتدائی طبی امداد", "زخمی", "بیمار",
            "خاندان رابطہ", "خاندان ملانا", "رشتہ دار", "فون", "گھر بات"
        ]
    else: # Default to English
        keywords_to_check = [
            "earthquake", "shaking", "quake", "tremor", "drop", "cover", "hold",
            "heatwave", "heat wave", "hot weather", "extreme heat", "safe", "hydrated", "sunlight",
            "wildfire", "forest fire", "fire approaching", "evacuate", "escape fire",
            "hurricane", "cyclone", "typhoon", "prepare", "preparation", "storm",
            "emergency kit", "survival kit", "go bag", "supplies", "what to pack",
            "protect home", "flood", "flooding", "flood proof", "prevent flood",
            "evacuation steps", "evacuate", "emergency exit", "leave building",
            "stay informed", "disaster updates", "news", "alerts", "information",
            "contact authorities", "local authorities", "government contact", "official number",
            "emergency number", "emergency contact", "help number", "sos", "1736",
            "rescue team", "rescue available", "rescuers", "help team",
            "drinking water", "safe water", "water safe", "potable water", "consume water",
            "medical help", "doctor", "clinic", "hospital", "first aid", "injury", "sick",
            "contact family", "family reunification", "find family", "relative", "phone family"
        ]

    # Check if any of the language-specific keywords are in the query
    if any(kw in query_lower for kw in keywords_to_check):
        return True

    # 3. If none of the above matched, return False (use RAG)
    return False

def get_general_response(query):
    """
    Generate appropriate responses for general chat, including hardcoded keyword-based Q&A.
    Checks for specific keyword matches first, then handles general greetings/phrases,
    and finally provides a fallback response.
    """
    query_lower = query.lower() # Normalize query for case-insensitive matching

    # Ensure session state has the language, default to English if not set
    if 'output_language' not in st.session_state:
        st.session_state.output_language = "English" # Default to English
    output_lang = st.session_state.output_language

    # --- Sindhi Responses ---
    if output_lang == "Sindhi":
        # --- Keyword-Based Q&A (Priority 1 - Specific Topics) ---
        if any(kw in query_lower for kw in ["زلزلي", "زلزلو", "لوڏا", "زمين تي ڪريو", "پناهه"]):
            return "زمين تي ڪريو، پناهه وٺو، ۽ لوڏا بند ٿيڻ تائين انتظار ڪريو."
        elif any(kw in query_lower for kw in ["گرمي جي لهر", "سخت گرمي", "محفوظ", "هائيڊريٽ", "پاڻي", "سج"]):
            return "هائيڊريٽ رهندا، سڌو سنئون سج کان بچندا، ۽ وڌ ۾ وڌ گرمي جي ڪلاڪن دوران اندر رهندا."
        elif any(kw in query_lower for kw in ["ٻيلهه جي باهه", "باهه ويجهو", "باهه", "نڪتو", "ڀڄڻ"]):
            return "جيڪڏهن هدايت ڏني وڃي ته فوري طور تي نڪتو ۽ باهه کان پري محفوظ علائقي ڏانهن هليو وڃو."
        elif any(kw in query_lower for kw in ["سامونڊي طوفان", "طوفان", "تياري"]):
            return "ٻاهران شين کي محفوظ ڪريو، ونڊوز کي مضبوط ڪريو، ۽ جيڪڏهن هدايت ڏني وڃي ته نيڪالي جا حڪم مڃيو."
        elif any(kw in query_lower for kw in ["ايمرجنسي کٽ", "سامان", "ڇا رکڻ"]):
            return "پاڻي، غير خراب ٿيڻ وارو کاڌو، ٽارچ، بيٽرين، پهرين مدد جو کٽ، ۽ ضروري دوائون."
        elif any(kw in query_lower for kw in ["گهر بچائڻ", "ٻوڏ", "ٻوڏ کان بچاء"]):
            return "جيڪڏهن توهان ٻوڏ جي خطري واري علائقي ۾ رهندا آهيو ته برقي آلات کي بلند ڪريو ۽ ٻوڏ جا رڪاوٽون لڳايو."
        elif any(kw in query_lower for kw in ["نيڪالي", "نڪرڻ", "ٻاهر وڃڻ", "ايمرجنسي قدم"]):
            return "پرسڪون رهو، نيڪالي جي رستن جي پيروي ڪريو، ۽ لفٽون استعمال نه ڪريو."
        elif any(kw in query_lower for kw in ["ڄاڻ رکڻ", "آفت جي خبرون", "خبرون", "الرٽس", "معلومات"]):
            return "مقامي خبرون ۽ موسم جي اپ ڊيٽس تي نظر رکندا، ۽ ايمرجنسي الرٽس لاءِ سائن اپ ڪندا."
        elif any(kw in query_lower for kw in ["مقامي اختيارين", "اختيارين رابطو", "سرڪاري نمبر", "حڪام"]):
             return "مقامي اختيارين لاءِ، توهان +92 335 5557362 سان رابطو ڪري سگهو ٿا."
        elif any(kw in query_lower for kw in ["ايمرجنسي نمبر", "ايمرجنسي رابطو", "مدد نمبر", "1736"]):
             return "ايمرجنسي حالتن ۾، مهرباني ڪري 1736 سان رابطو ڪريو."
        elif any(kw in query_lower for kw in ["ريسڪيو ٽيم", "ريسڪيو", "بچاء ٽيم", "مدد ٽيم"]):
             return "ها، ريسڪيو ٽيمون موجود آهن. توهان انهن سان 1736 يا +92 335 5557362 تي رابطو ڪري سگهو ٿا."
        elif any(kw in query_lower for kw in ["پيئڻ جو پاڻي", "صاف پاڻي", "پاڻي محفوظ", "پاڻي پيئڻ"]):
             return "اسان پيئڻ لاءِ هتي فراهم ڪيل بوتل جو پاڻي استعمال ڪرڻ جي صلاح ڏيون ٿا. ٻوڏ جو پاڻي استعمال ڪرڻ کان پاسو ڪريو ڇاڪاڻ ته اهو آلودگي ٿي سگهي ٿو."
        elif any(kw in query_lower for kw in ["طبي مدد", "ڊاڪٽر", "ڪلينڪ", "اسپتال", "پهرين مدد", "زخمي", "بيمار"]):
             return "طبي ڪلينڪ سينٽر جي ڏکڻ ونگ ۾ واقع آهي. نشانين جي پيروي ڪريو يا اسان جي عملي کان هدايتون پڇو."
        elif any(kw in query_lower for kw in ["خاندان رابطو", "خاندان ملائڻ", "رشتيدار", "فون", "گهر ڳالهايو"]):
             return "اسان وٽ خاندان جي ٻيهر ملاپ لاءِ سهولتون آهن. مهرباني ڪري مدد لاءِ استقباليه تي تفصيل فراهم ڪريو."

        # --- Greetings and Common Phrases (Priority 2 - General Chat) ---
        # Check simple phrases exactly if they weren't caught by keywords
        query_lower_stripped = query_lower.strip() # For exact match check
        if query_lower_stripped in ['hi', 'hello', 'hey', 'هيلو', 'سلام']:
             return "السلام عليڪم! مان توهان جو آفتن جي انتظام جو مددگار آهيان. مان توهان جي ڪهڙي مدد ڪري سگهان ٿو؟"
        elif query_lower_stripped in ['good morning', 'good afternoon', 'good evening', 'صبح بخير', 'شام بخير']:
             return "توهان جو مهرباني! مان توهان جي آفتن جي انتظام جي سوالن ۾ مدد ڪرڻ لاءِ حاضر آهيان."
        elif query_lower_stripped in ['how are you', 'ڪيئن آهيو', 'حال ڪيئن آهي']:
             return "مان ٺيڪ آهيان، توهان جي پڇڻ جو مهرباني! مان آفتن جي انتظام جي معلومات ڏيڻ لاءِ تيار آهيان."
        elif query_lower_stripped in ['thank', 'thanks', 'مهرباني', 'شڪريه']: # Added thanks
             return "توهان جو مهرباني! آفتن جي انتظام بابت ڪو به سوال پڇڻ لاءِ آزاد محسوس ڪريو."
        elif query_lower_stripped in ['bye', 'goodbye', 'خدا حافظ', 'الوداع']:
             return "خدا حافظ! جيڪڏهن توهان کي آفتن جي انتظام بابت وڌيڪ سوال هجن ته پوءِ ضرور پڇو."
        elif query_lower_stripped in ['who are you', 'تون ڪير آهين', 'توهان جو نالو ڇا آهي']:
             return "مان هڪ خاص آفتن جي انتظام جو مددگار آهيان. مان آفتن جي انتظام، حفاظتي اپاءَ ۽ آفتن جي جواب جي حڪمت عملي بابت معلومات ڏئي سگهان ٿو."
        # Fallback if keywords didn't match but might contain parts of greetings
        elif any(greeting in query_lower for greeting in ['hi', 'hello', 'hey', 'هيلو', 'سلام']):
            return "السلام عليڪم! مان توهان جو آفتن جي انتظام جو مددگار آهيان. مان توهان جي ڪهڙي مدد ڪري سگهان ٿو؟"
        elif any(time in query_lower for time in ['good morning', 'good afternoon', 'good evening', 'صبح بخير', 'شام بخير']):
            return "توهان جو مهرباني! مان توهان جي آفتن جي انتظام جي سوالن ۾ مدد ڪرڻ لاءِ حاضر آهيان."
        elif 'how are you' in query_lower or 'ڪيئن آهيو' in query_lower or 'حال ڪيئن آهي' in query_lower:
            return "مان ٺيڪ آهيان، توهان جي پڇڻ جو مهرباني! مان آفتن جي انتظام جي معلومات ڏيڻ لاءِ تيار آهيان."
        elif 'thank' in query_lower or 'مهرباني' in query_lower or 'شڪريه' in query_lower:
            return "توهان جو مهرباني! آفتن جي انتظام بابت ڪو به سوال پڇڻ لاءِ آزاد محسوس ڪريو."
        elif 'bye' in query_lower or 'goodbye' in query_lower or 'خدا حافظ' in query_lower or 'الوداع' in query_lower:
            return "خدا حافظ! جيڪڏهن توهان کي آفتن جي انتظام بابت وڌيڪ سوال هجن ته پوءِ ضرور پڇو."
        elif 'who are you' in query_lower or 'تون ڪير آهين' in query_lower or 'توهان جو نالو ڇا آهي' in query_lower:
            return "مان هڪ خاص آفتن جي انتظام جو مددگار آهيان. مان آفتن جي انتظام، حفاظتي اپاءَ ۽ آفتن جي جواب جي حڪمت عملي بابت معلومات ڏئي سگهان ٿو."

        # --- General Fallback (Priority 3 - If nothing else matches) ---
        else:
            # Return the default fallback if no keyword or greeting was substantially matched
            return "مان آفتن جي انتظام جي معاملن ۾ ماهر آهيان. عام موضوعن تي مدد نه ڪري سگهندس، پر آفتن جي انتظام، ايمرجنسي طريقن يا حفاظتي اپاءَ بابت ڪو به سوال پڇڻ لاءِ آزاد محسوس ڪريو."


    # --- Urdu Responses ---
    elif output_lang == "Urdu":
        # --- Keyword-Based Q&A (Priority 1 - Specific Topics) ---
        if any(kw in query_lower for kw in ["زلزلے", "زلزلہ", "جھٹکے", "گر جائیں", "پناہ"]):
            return "زمین پر گر جائیں، پناہ لیں، اور جھٹکے رکنے تک انتظار کریں۔"
        elif any(kw in query_lower for kw in ["گرمی کی لہر", "شدید گرمی", "محفوظ", "ہائیڈریٹ", "پانی", "دھوپ"]):
             return "ہائیڈریٹ رہیں، براہ راست دھوپ سے بچیں، اور زیادہ گرمی کے اوقات میں اندر رہیں۔"
        elif any(kw in query_lower for kw in ["جنگل کی آگ", "آگ قریب", "آگ", "نکلو", "بھاگنا"]):
             return "اگر ہدایت دی جائے تو فوراً نکلو اور آگ سے دور محفوظ علاقے میں چلے جائیں۔"
        elif any(kw in query_lower for kw in ["سمندری طوفان", "طوفان", "تیاری"]):
             return "باہر کے اشیاء کو محفوظ کریں، کھڑکیوں کو مضبوط کریں، اور اگر ہدایت دی جائے تو نکاسی کے احکامات پر عمل کریں۔"
        elif any(kw in query_lower for kw in ["ایمرجنسی کٹ", "سامان", "کیا رکھنا"]):
             return "پانی، غیر خراب ہونے والا کھانا، ٹارچ، بیٹریاں، ابتدائی طبی امداد کا کٹ، اور ضروری ادویات۔"
        elif any(kw in query_lower for kw in ["گھر بچانا", "سیلاب", "سیلاب سے بچاؤ"]):
             return "اگر آپ سیلاب کے خطرے والے علاقے میں رہتے ہیں تو بجلی کے آلات کو بلند کریں اور سیلاب کی رکاوٹیں لگائیں۔"
        elif any(kw in query_lower for kw in ["نکاسی", "نکلنا", "باہر جانا", "ایمرجنسی اقدامات"]):
             return "پرسکون رہیں، نکاسی کے راستوں کی پیروی کریں، اور لفٹوں کا استعمال نہ کریں۔"
        elif any(kw in query_lower for kw in ["مطلع رہنا", "آفت کی خبریں", "خبریں", "الرٹس", "معلومات"]):
             return "مقامی خبریں اور موسمی اپ ڈیٹس دیکھتے رہیں، اور ایمرجنسی الرٹس کے لئے سائن اپ کریں۔"
        elif any(kw in query_lower for kw in ["مقامی حکام", "حکام رابطہ", "سرکاری نمبر", "حکومت"]):
             return "مقامی حکام کے لئے، آپ +92 335 5557362 سے رابطہ کر سکتے ہیں۔"
        elif any(kw in query_lower for kw in ["ایمرجنسی نمبر", "ایمرجنسی رابطہ", "مدد نمبر", "1736"]):
             return "ہنگامی صورتحال میں، براہ کرم 1736 سے رابطہ کریں۔"
        elif any(kw in query_lower for kw in ["ریسکیو ٹیم", "ریسکیو", "بچاؤ ٹیم", "مدد ٹیم"]):
             return "جی ہاں، ریسکیو ٹیمیں دستیاب ہیں۔ آپ ان سے 1736 یا +92 335 5557362 پر رابطہ کر سکتے ہیں۔"
        elif any(kw in query_lower for kw in ["پینے کا پانی", "صاف پانی", "پانی محفوظ", "پانی پینا"]):
             return "ہم پینے کے لئے یہاں دی گئی بوتل پانی کا استعمال کرنے کی تجویز دیتے ہیں۔ براہ کرم سیلاب کے پانی کو نہ پیں کیونکہ یہ آلودہ ہو سکتا ہے۔"
        elif any(kw in query_lower for kw in ["طبی مدد", "ڈاکٹر", "کلینک", "ہسپتال", "ابتدائی طبی امداد", "زخمی", "بیمار"]):
             return "طبی کلینک مرکز کے جنوبی ونگ میں واقع ہے۔ نشانیوں کی پیروی کریں یا ہمارے عملے سے رہنمائی کے لئے پوچھیں۔"
        elif any(kw in query_lower for kw in ["خاندان رابطہ", "خاندان ملانا", "رشتہ دار", "فون", "گھر بات"]):
             return "ہمارے پاس خاندان کے ملاپ کے لیے سہولیات ہیں۔ براہ کرم مدد کے لیے استقبالیہ پر تفصیلات فراہم کریں۔"

        # --- Greetings and Common Phrases (Priority 2 - General Chat) ---
        # Check simple phrases exactly if they weren't caught by keywords
        query_lower_stripped = query_lower.strip() # For exact match check
        if query_lower_stripped in ['hi', 'hello', 'hey', 'ہیلو', 'سلام']:
             return "السلام علیکم! میں آپ کا آفات کے انتظام کا مددگار ہوں۔ میں آپ کی کیا مدد کر سکتا ہوں؟"
        elif query_lower_stripped in ['good morning', 'good afternoon', 'good evening', 'صبح بخیر', 'شام بخیر']:
             return "آپ کا شکریہ! میں آپ کی آفات کے انتظام کے سوالات میں مدد کرنے کے لیے حاضر ہوں۔"
        elif query_lower_stripped in ['how are you', 'آپ کیسے ہیں', 'کیا حال ہے']:
             return "میں ٹھیک ہوں، آپ کی پوچھنے کا شکریہ! میں آفات کے انتظام کی معلومات دینے کے لیے تیار ہوں۔"
        elif query_lower_stripped in ['thank', 'thanks', 'شکریہ', 'مہربانی']: # Added thanks
             return "آپ کا شکریہ! آفات کے انتظام کے بارے میں کوئی بھی سوال پوچھنے کے لیے آزاد محسوس کریں۔"
        elif query_lower_stripped in ['bye', 'goodbye', 'خدا حافظ', 'الوداع']:
             return "خدا حافظ! اگر آپ کو آفات کے انتظام کے بارے میں مزید سوالات ہوں تو ضرور پوچھیں۔"
        elif query_lower_stripped in ['who are you', 'آپ کون ہیں', 'آپ کا نام کیا ہے']:
             return "میں ایک خصوصی آفات کے انتظام کا مددگار ہوں۔ میں آفات کے انتظام، حفاظتی اقدامات اور آفات کے جواب کی حکمت عملی کے بارے میں معلومات دے سکتا ہوں۔"
        # Fallback if keywords didn't match but might contain parts of greetings
        elif any(greeting in query_lower for greeting in ['hi', 'hello', 'hey', 'ہیلو', 'سلام']):
            return "السلام علیکم! میں آپ کا آفات کے انتظام کا مددگار ہوں۔ میں آپ کی کیا مدد کر سکتا ہوں؟"
        elif any(time in query_lower for time in ['good morning', 'good afternoon', 'good evening', 'صبح بخیر', 'شام بخیر']):
            return "آپ کا شکریہ! میں آپ کی آفات کے انتظام کے سوالات میں مدد کرنے کے لیے حاضر ہوں۔"
        elif 'how are you' in query_lower or 'آپ کیسے ہیں' in query_lower or 'کیا حال ہے' in query_lower:
            return "میں ٹھیک ہوں، آپ کی پوچھنے کا شکریہ! میں آفات کے انتظام کی معلومات دینے کے لیے تیار ہوں۔"
        elif 'thank' in query_lower or 'شکریہ' in query_lower or 'مہربانی' in query_lower:
            return "آپ کا شکریہ! آفات کے انتظام کے بارے میں کوئی بھی سوال پوچھنے کے لیے آزاد محسوس کریں۔"
        elif 'bye' in query_lower or 'goodbye' in query_lower or 'خدا حافظ' in query_lower or 'الوداع' in query_lower:
            return "خدا حافظ! اگر آپ کو آفات کے انتظام کے بارے میں مزید سوالات ہوں تو ضرور پوچھیں۔"
        elif 'who are you' in query_lower or 'آپ کون ہیں' in query_lower or 'آپ کا نام کیا ہے' in query_lower:
            return "میں ایک خصوصی آفات کے انتظام کا مددگار ہوں۔ میں آفات کے انتظام، حفاظتی اقدامات اور آفات کے جواب کی حکمت عملی کے بارے میں معلومات دے سکتا ہوں۔"

        # --- General Fallback (Priority 3 - If nothing else matches) ---
        else:
            # Return the default fallback if no keyword or greeting was substantially matched
            return "میں آفات کے انتظام کے معاملات میں ماہر ہوں۔ عام موضوعات پر مدد نہیں کر سکتا، لیکن آفات کے انتظام، ایمرجنسی طریقوں یا حفاظتی اقدامات کے بارے میں کوئی بھی سوال پوچھنے کے لیے آزاد محسوس کریں۔"


    # --- English Responses (Default) ---
    else:
        # --- Keyword-Based Q&A (Priority 1 - Specific Topics) ---
        if any(kw in query_lower for kw in ["earthquake", "shaking", "quake", "tremor", "drop", "cover", "hold"]):
             return "Drop, cover, and hold on until the shaking stops."
        elif any(kw in query_lower for kw in ["heatwave", "heat wave", "hot weather", "extreme heat", "safe", "hydrated", "sunlight"]):
             return "Stay hydrated, avoid direct sunlight, and stay indoors during peak heat hours."
        elif any(kw in query_lower for kw in ["wildfire", "forest fire", "fire approaching", "evacuate", "escape fire"]):
             return "Evacuate immediately if instructed, and move to a safe area away from the fire."
        elif any(kw in query_lower for kw in ["hurricane", "cyclone", "typhoon", "prepare", "preparation", "storm"]):
             return "Secure outdoor objects, reinforce windows, and follow evacuation orders if given."
        elif any(kw in query_lower for kw in ["emergency kit", "survival kit", "go bag", "supplies", "what to pack"]):
             return "Water, non-perishable food, flashlight, batteries, first aid kit, and essential medications."
        elif any(kw in query_lower for kw in ["protect home", "flood", "flooding", "flood proof", "prevent flood"]):
             return "Elevate electrical appliances and install flood barriers if you live in a flood-prone area."
        elif any(kw in query_lower for kw in ["evacuation steps", "evacuate", "emergency exit", "leave building"]):
             return "Stay calm, follow evacuation routes, and do not use elevators."
        elif any(kw in query_lower for kw in ["stay informed", "disaster updates", "news", "alerts", "information"]):
             return "Monitor local news and weather updates, and sign up for emergency alerts."
        elif any(kw in query_lower for kw in ["contact authorities", "local authorities", "government contact", "official number"]):
             return "For local authorities, you can contact +92 335 5557362."
        elif any(kw in query_lower for kw in ["emergency number", "emergency contact", "help number", "sos", "1736"]):
             return "For emergencies, please contact 1736."
        elif any(kw in query_lower for kw in ["rescue team", "rescue available", "rescuers", "help team"]):
             return "Yes, rescue teams are available. You can contact them at 1736 or +92 335 5557362."
        elif any(kw in query_lower for kw in ["drinking water", "safe water", "water safe", "potable water", "consume water"]):
             return "We advise using bottled water provided here for drinking. Avoid consuming floodwater as it may be contaminated."
        elif any(kw in query_lower for kw in ["medical help", "doctor", "clinic", "hospital", "first aid", "injury", "sick"]):
             return "The medical clinic is located in the south wing of the center. Follow the signs or ask our staff for directions."
        elif any(kw in query_lower for kw in ["contact family", "family reunification", "find family", "relative", "phone family"]):
             return "We have facilities for family reunification. Please provide details at the reception for assistance."

        # --- Greetings and Common Phrases (Priority 2 - General Chat) ---
        # Check simple phrases exactly if they weren't caught by keywords
        query_lower_stripped = query_lower.strip() # For exact match check
        if query_lower_stripped in ['hi', 'hello', 'hey']:
            return "Hello! I'm your disaster management assistant. How can I help you today?"
        elif query_lower_stripped in ['good morning', 'good afternoon', 'good evening']:
            return "Thank you! I'm here to help you with disaster management related questions."
        elif query_lower_stripped == 'how are you':
            return "I'm functioning well, thank you for asking! I'm ready to help you with disaster management information."
        elif query_lower_stripped in ['thank', 'thanks', 'thank you']:
            return "You're welcome! Feel free to ask any questions about disaster management."
        elif query_lower_stripped in ['bye', 'goodbye']:
            return "Goodbye! If you have more questions about disaster management later, feel free to ask."
        elif query_lower_stripped in ['who are you', 'what is your name']:
            return "I'm a specialized chatbot designed to help with disaster management information and procedures. I can answer questions about emergency protocols, safety measures, and disaster response strategies."
        # Fallback if keywords didn't match but might contain parts of greetings
        elif any(greeting in query_lower for greeting in ['hi', 'hello', 'hey']):
            return "Hello! I'm your disaster management assistant. How can I help you today?"
        elif any(time in query_lower for time in ['good morning', 'good afternoon', 'good evening']):
            return "Thank you! I'm here to help you with disaster management related questions."
        elif 'how are you' in query_lower:
            return "I'm functioning well, thank you for asking! I'm ready to help you with disaster management information."
        elif 'thank' in query_lower or 'thanks' in query_lower:
            return "You're welcome! Feel free to ask any questions about disaster management."
        elif 'bye' in query_lower or 'goodbye' in query_lower:
            return "Goodbye! If you have more questions about disaster management later, feel free to ask."
        elif 'who are you' in query_lower or 'what is your name' in query_lower:
            return "I'm a specialized chatbot designed to help with disaster management information and procedures. I can answer questions about emergency protocols, safety measures, and disaster response strategies."

        # --- General Fallback (Priority 3 - If nothing else matches) ---
        else:
            # Return the default fallback if no keyword or greeting was substantially matched
            return "I'm specialized in disaster management topics. While I can't help with general topics, I'd be happy to answer any questions about disaster management, emergency procedures, or safety protocols."


@st.cache_resource # Cache the RAG chain resource
def initialize_rag():
    """Initializes the RAG system (LLM, Embeddings, VectorStore, QA Chain)."""
    try:
        st.write("Initializing RAG system...") # Debug output
        # API Keys from secrets
        PINECONE_API_KEY = st.secrets.get("PINECONE_API_KEY")
        GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY")

        if not GOOGLE_API_KEY or not PINECONE_API_KEY:
            st.error("🔴 Critical Error: API keys (GOOGLE_API_KEY, PINECONE_API_KEY) not found in Streamlit secrets.")
            st.stop()

        genai.configure(api_key=GOOGLE_API_KEY)

        # Initialize embeddings safely
        try:
            embeddings = HuggingFaceEmbeddings(
                model_name='all-MiniLM-L6-v2',
                # model_kwargs={'device': 'cpu'}, # Let HuggingFace decide optimal device
                # encode_kwargs={'normalize_embeddings': True} # Normalization often default/handled
            )
            st.write("Embeddings initialized.") # Debug output
        except Exception as e:
            st.error(f"🔴 Error initializing embeddings: {str(e)}")
            st.stop()

        # Initialize Pinecone safely
        try:
            from pinecone import Pinecone, exceptions as pinecone_exceptions
            pc = Pinecone(api_key=PINECONE_API_KEY)
            index_name = "pdfinfo" # Make sure this index exists in your Pinecone project

            # Check if index exists
            if index_name not in pc.list_indexes().names:
                 st.error(f"🔴 Pinecone index '{index_name}' does not exist. Please create it in your Pinecone console.")
                 st.stop()

            pinecone_index = pc.Index(index_name)
            # Optionally, check index stats to confirm connection
            # pinecone_index.describe_index_stats()

            vectorstore = PineconeVectorStore(
                index=pinecone_index,
                embedding=embeddings,
                text_key="text" # Ensure this matches the metadata key used during indexing
            )
            st.write(f"Pinecone vector store connected to index '{index_name}'.") # Debug output
        except pinecone_exceptions.ApiException as e:
            st.error(f"🔴 Pinecone API Error: {e}. Check API key and index name.")
            st.stop()
        except Exception as e:
            st.error(f"🔴 Error connecting to Pinecone: {str(e)}")
            st.stop()

        # Initialize Gemini LLM safely
        try:
            llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash", # Use a stable model like gemini-1.5-flash
                temperature=0.2, # Slightly increased for potentially better RAG results
                google_api_key=GOOGLE_API_KEY,
                # max_retries=3, # Handled internally by langchain-google-genai
                # timeout=30, # Handled internally
                max_output_tokens=2048,
                convert_system_message_to_human=True # Often helpful for Gemini models
            )
            st.write("Google Generative AI LLM initialized.") # Debug output
        except Exception as e:
            st.error(f"🔴 Error initializing LLM: {str(e)}")
            st.stop()

        # Define the prompt template (outside the chain for clarity)
        # Use f-string within the function call that uses the chain if language changes often
        prompt_template_str = """You are a knowledgeable and helpful disaster management assistant.
        Your primary goal is to provide accurate information based *only* on the provided context.
        If the context does not contain the answer, clearly state that you don't have the specific information from the provided documents but offer general knowledge if appropriate for disaster management.
        Do *not* invent procedures, contact numbers, or specific details not present in the context.
        Be empathetic and professional.

        {language_instruction}

        Context:
        {context}

        Question: {question}

        Answer:"""

        QA_PROMPT = PromptTemplate(
            template=prompt_template_str,
            input_variables=["context", "question", "language_instruction"]
        )

        # Create the QA chain safely
        try:
            qa_chain = RetrievalQA.from_chain_type(
                llm=llm,
                chain_type="stuff", # Simple chain type
                retriever=vectorstore.as_retriever(search_kwargs={"k": 5}), # Retrieve top 5 documents
                return_source_documents=True, # Return sources for potential debugging/display
                chain_type_kwargs={"prompt": QA_PROMPT}
            )
            st.write("RetrievalQA chain created.") # Debug output
            st.success("✅ RAG System Initialized Successfully!")
            return qa_chain
        except Exception as e:
            st.error(f"🔴 Error creating QA chain: {str(e)}")
            st.stop()

    except Exception as e:
        st.error(f"🔴 Fatal Error during RAG initialization: {str(e)}")
        st.stop()

def get_rag_response(qa_chain, query):
    """
    Get a response from the RAG system for a domain-specific query.
    """
    if qa_chain is None:
         return "Sorry, the RAG system is not available."
    try:
        # Get language-specific instructions based on the current output language
        lang_instruction = get_language_prompt(st.session_state.output_language)

        # Invoke the chain with the query and language instruction
        response = qa_chain.invoke({
            "query": query,
            "language_instruction": lang_instruction
            })

        # Log source documents for debugging if needed
        # st.write("Source Documents:", response.get('source_documents', []))

        return response['result']
    except Exception as e:
        st.error(f"Error during RAG inference: {str(e)}")
        # Provide a user-friendly error message
        if "deadline exceeded" in str(e).lower():
            return "Sorry, the request took too long to process. Please try again."
        elif "api key not valid" in str(e).lower():
             return "Sorry, there seems to be an issue with the AI service configuration. Please contact support."
        else:
            return f"I encountered an error trying to answer that. Please try rephrasing your question. (Error: {str(e)[:100]}...)"


def main():
    """Main function to run the Streamlit application."""
    # Page config (set only once)
    st.set_page_config(
        page_title="Disaster Management RAG Chatbot",
        page_icon="🚨",
        layout="wide"
    )

    # --- Load CSS --- (Consider moving to a separate CSS file)
    st.markdown("""
        <style>
        /* Main container styling */
        .main .block-container { /* Target block container within main */
            padding-top: 2rem; /* Adjust top padding */
            padding-bottom: 2rem;
            padding-left: 1rem;
            padding-right: 1rem;
            max-width: 1200px; /* Control max width */
            margin: 0 auto; /* Center the container */
        }

        /* Chat container styling (if you want specific chat area width) */
        /* .stChatInputContainer, .stChatMessage { max-width: 800px; margin: 0 auto; } */

        /* Sidebar styling */
        [data-testid="stSidebar"] {
            padding: 1rem;
            background-color: #f0f2f6; /* Lighter sidebar */
        }

        /* Buttons */
        div.stButton > button {
            width: 100%;
            border-radius: 8px !important;
            margin: 0.2rem 0 !important;
            border: 1px solid #d0d0d0 !important;
            background-color: #ffffff !important;
            color: #333333 !important; /* Darker text for light background */
        }
         div.stButton > button:hover {
            background-color: #e8e8e8 !important;
            border-color: #b0b0b0 !important;
        }
        /* Primary button */
         div.stButton > button[kind="primary"] {
            background-color: #007bff !important; /* Standard blue */
            color: white !important;
            border: none !important;
         }
         div.stButton > button[kind="primary"]:hover {
            background-color: #0056b3 !important;
         }

        /* Section headers in sidebar */
        .section-header {
            color: #555555 !important;
            font-size: 0.8rem !important;
            font-weight: 600 !important;
            margin: 1rem 0 0.5rem 0 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.5px !important;
        }

        /* Expander styling */
        .stExpander {
            border: 1px solid #e0e0e0 !important;
            border-radius: 8px !important;
            background-color: #ffffff !important;
            margin-bottom: 0.5rem !important;
        }
        .stExpander header {
             font-weight: 500 !important;
             color: #333333 !important;
             border-radius: 8px 8px 0 0 !important; /* Match top corners */
        }
        .stExpander div[data-testid="stExpanderDetails"] {
            background-color: #ffffff !important; /* Keep content white */
             border-radius: 0 0 8px 8px !important; /* Match bottom corners */
        }


        /* Thinking animation */
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .thinking-container { display: flex; align-items: center; gap: 0.5rem; color: #555555; font-style: italic;}
        .thinking-spinner { width: 14px; height: 14px; border: 2px solid #cccccc; border-top: 2px solid #555555; border-radius: 50%; animation: spin 1s linear infinite; }

        /* Main heading */
        .main-heading {
            text-align: center;
            color: #007bff; /* Blue heading */
            font-weight: 600;
            margin-bottom: 1.5rem;
            font-size: 2rem; /* Default size */
        }
        @media screen and (max-width: 768px) { .main-heading { font-size: 1.6rem; margin-bottom: 1rem; } }
        @media screen and (max-width: 480px) { .main-heading { font-size: 1.4rem; margin-bottom: 0.8rem; } }

        /* Ensure chat messages wrap */
         .stChatMessage { white-space: pre-wrap; word-wrap: break-word; }

        </style>
    """, unsafe_allow_html=True)

    # --- Display Heading ---
    st.markdown('<h1 class="main-heading">🚨 Disaster Management Assistant</h1>', unsafe_allow_html=True)

    # --- Authentication ---
    # This assumes auth_page handles showing login/signup and returns (True, user_data) or (False, None)
    # Ensure FirebaseAuthenticator is initialized correctly within auth.authenticator
    try:
        is_authenticated, user = auth_page()
    except Exception as auth_error:
        st.error(f"Authentication error: {auth_error}")
        st.stop() # Stop execution if authentication fails critically

    if not is_authenticated or user is None:
        st.info("Please log in or sign up to use the chatbot.")
        return # Stop further execution if not authenticated

    # --- User is Authenticated ---
    user_id = user.get('uid')
    if not user_id:
         st.error("User ID not found after authentication. Please try logging in again.")
         return

    # Load user preferences (e.g., language) - This needs implementation in auth.ui
    # preferences = load_user_preferences(user)
    # Apply preferences if available
    # st.session_state.input_language = preferences.get('input_language', 'English')
    # st.session_state.output_language = preferences.get('output_language', 'English')

    # Load chat history for the current session
    history_manager = ChatHistoryManager()
    if st.session_state.current_session_id is None:
         # Load the latest session or create a new one if none exists
         latest_session_id = history_manager.get_latest_session_id(user_id)
         if latest_session_id:
             st.session_state.current_session_id = latest_session_id
             st.session_state.messages = history_manager.load_chat_history(user_id, latest_session_id)
         else:
             st.session_state.current_session_id = history_manager.create_new_session(user_id)
             st.session_state.messages = []


    # --- Initialize RAG System (Cached) ---
    # This will only run once per session or until the cache is cleared
    qa_chain = initialize_rag()


    # --- Sidebar ---
    with st.sidebar:
        st.markdown(f"**Welcome, {user.get('email', 'User')}!**")
        st.divider()

        if st.session_state.get('show_settings', False):
            st.subheader("⚙️ User Settings")
            if st.button("← Back to Chat"):
                st.session_state.show_settings = False
                st.rerun()
            # Assuming user_sidebar is implemented in auth.ui
            user_sidebar(user) # Pass user data to display/edit settings
        else:
            # New Chat Button
            if st.button("✨ New Conversation", type="primary", use_container_width=True):
                session_id = history_manager.create_new_session(user_id)
                st.session_state.messages = []
                st.session_state.current_session_id = session_id
                st.experimental_rerun() # Use experimental rerun for cleaner state update

            # Chat History Display
            chat_history_sidebar(user_id) # Assumes this handles displaying sessions

            st.divider()

            # Language Settings Expander
            with st.expander("🌐 Language Settings", expanded=False):
                # Input language (optional, can be inferred)
                # input_lang_options = ["English", "Urdu", "Sindhi"]
                # current_input_lang_index = input_lang_options.index(st.session_state.input_language)
                # input_language = st.selectbox(
                #     "Input Language", input_lang_options, index=current_input_lang_index, key="input_lang_select"
                # )
                # if input_language != st.session_state.input_language:
                #     st.session_state.input_language = input_language
                #     # save_user_preferences(user_id) # Add function to save preference

                # Output language
                output_lang_options = ["English", "Urdu", "Sindhi"]
                current_output_lang_index = output_lang_options.index(st.session_state.output_language)
                output_language = st.selectbox(
                    "Bot Response Language", output_lang_options, index=current_output_lang_index, key="output_lang_select"
                )
                if output_language != st.session_state.output_language:
                    st.session_state.output_language = output_language
                    st.success(f"Response language set to {output_language}")
                    # save_user_preferences(user_id) # Add function to save preference
                    st.experimental_rerun() # Rerun to apply immediately


            # About Section Expander
            with st.expander("ℹ️ About This Bot", expanded=False):
                 st.markdown("""
                 This assistant provides information on disaster management using advanced AI.
                 - **AI Model:** Google Gemini
                 - **Data Source:** Indexed documents via Pinecone
                 - **Framework:** LangChain & Streamlit
                 Ask questions about emergency protocols, safety measures, and disaster response.
                 """)

            st.divider()

            # Profile Button
            if st.button("👤 Profile / Settings"):
                st.session_state.show_settings = True
                st.experimental_rerun()

            st.divider()

            # Download Options
            st.markdown('<div class="section-header">Export Chat</div>', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                 pdf_bytes = create_chat_pdf()
                 if pdf_bytes:
                     st.download_button(
                        label="📄 PDF",
                        data=pdf_bytes,
                        file_name=f"chat_{st.session_state.current_session_id or 'current'}_{datetime.now():%Y%m%d_%H%M}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                 else:
                      st.button("📄 PDF", disabled=True, use_container_width=True) # Disable if error
            with col2:
                 txt_bytes = create_chat_text()
                 if txt_bytes:
                     st.download_button(
                        label="📝 Text",
                        data=txt_bytes,
                        file_name=f"chat_{st.session_state.current_session_id or 'current'}_{datetime.now():%Y%m%d_%H%M}.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
                 else:
                     st.button("📝 Text", disabled=True, use_container_width=True) # Disable if error


    # --- Main Chat Area ---

    # Display existing chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"]) # Use markdown for potential formatting

    # Email UI Container (appears below messages)
    email_ui_container = st.container()
    with email_ui_container:
        user_email = user.get('email', 'anonymous@example.com') # Get user email safely
        # show_email_ui(st.session_state.messages, user_email) # Pass messages and email

    # Handle new chat input
    if prompt := st.chat_input("Ask about disaster management..."):
        # 1. Append and Display User Message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 2. Sync User Message to DB (if session ID exists)
        if st.session_state.current_session_id:
            try:
                metadata = { 'language': st.session_state.input_language, 'timestamp': datetime.now().isoformat() }
                sync_chat_message(user_id, st.session_state.current_session_id, "user", prompt, metadata)
            except Exception as sync_error:
                st.warning(f"Could not sync user message: {sync_error}") # Non-critical warning


        # 3. Get and Display Bot Response
        with st.chat_message("assistant"):
            response = ""
            message_placeholder = st.empty()
            # Show thinking animation
            message_placeholder.markdown('<div class="thinking-container"><div class="thinking-spinner"></div> Thinking...</div>', unsafe_allow_html=True)

            try:
                # Decide which response function to use based on keywords/phrases
                if should_use_general_response(prompt):
                    response = get_general_response(prompt)
                else:
                    # Ensure qa_chain is initialized before calling RAG
                    if qa_chain:
                         response = get_rag_response(qa_chain, prompt)
                    else:
                         response = "Sorry, the information retrieval system is currently unavailable."

                # Display the final response
                message_placeholder.markdown(response)

                # 4. Append Bot Response to Session State
                st.session_state.messages.append({"role": "assistant", "content": response})

                # 5. Sync Bot Response to DB (if session ID exists)
                if st.session_state.current_session_id:
                    try:
                        metadata = {
                            'language': st.session_state.output_language,
                            'timestamp': datetime.now().isoformat(),
                            'type': 'general' if should_use_general_response(prompt) else 'rag'
                        }
                        sync_chat_message(user_id, st.session_state.current_session_id, "assistant", response, metadata)
                    except Exception as sync_error:
                        st.warning(f"Could not sync assistant message: {sync_error}") # Non-critical warning

            except Exception as e:
                st.error(f"An error occurred: {e}")
                error_message = "Sorry, I encountered a problem while processing your request."
                message_placeholder.markdown(error_message)
                st.session_state.messages.append({"role": "assistant", "content": error_message})
                # Optionally sync error message to DB
                if st.session_state.current_session_id:
                     try:
                         sync_chat_message(user_id, st.session_state.current_session_id, "assistant", error_message, {'type': 'error'})
                     except Exception as sync_error:
                         st.warning(f"Could not sync error message: {sync_error}")

            # Optional: Rerun might not be needed unless explicitly updating UI elements like email
            # st.experimental_rerun()


# --- Run the App ---
if __name__ == "__main__":
    # Note: Ensure you have firebase_config.json and necessary environment variables/secrets set up
    # Initialize Firebase Admin SDK if needed by your auth backend *before* calling auth functions
    # e.g., if not firebase_admin._apps: firebase_admin.initialize_app(...)
    main()
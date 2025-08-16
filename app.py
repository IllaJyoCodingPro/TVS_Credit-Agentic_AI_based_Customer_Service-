from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import google.generativeai as genai

# ---------------------------------------------------------
# 🔑 Paste your Gemini API Key here directly
# ---------------------------------------------------------
GEMINI_API_KEY = "paste your api key"

# Configure Gemini
use_gemini = False
model = None
if GEMINI_API_KEY.strip() != "":
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        # ✅ Updated model (old "gemini-pro" is deprecated)
        model = genai.GenerativeModel("gemini-1.5-flash")
        print("✅ Gemini API Key loaded & model initialized.")
        use_gemini = True
    except Exception as e:
        print("⚠️ Failed to initialize Gemini:", e)
else:
    print("⚠️ No Gemini API Key found. Using FAQ fallback only.")

app = Flask(__name__)
CORS(app)

# Conversation memory
conversation_memory = {}

# -----------------------------
# FAQ fallback dataset
# -----------------------------
faq_data = {
    # 👋 Entry Point
    "hi": "Hi there! This is Tia, your virtual assistant! 👋\nPlease choose:\n- New Customer\n- Existing Customer\n- Employee\n- Channel Partner\n- Change Language",

    # ---------------- New Customer Flow ----------------
    "new customer": "Choose the product of your interest:\n- Two Wheeler Loans\n- Used Car Loans\n- Tractor Loans\n- Personal Loans\n- Consumer Durable Loans\n- Gold Loans\n- Loan Against Property",

    # Two Wheeler Loan
    "two wheeler loans": "🚲 Two-Wheeler Loan:\nFeatures & Benefits:\n-> 2-minute loan approval\n-> Up to 95% funding\n-> Attractive interest rates\n-> Minimal documentation\n-> Flexible repayment\n👉 [Apply Now](https://www.tvscredit.com/loans/two-wheeler-loans/apply-now/?utm_source=Chatbot&utm_medium=TWApplyloan&CC=WC&AC=TVSCS)\n\nWhat would you like to do next? (Eligibility / Documents / Main Menu)",

    "two wheeler eligibility": "Eligibility for Two-Wheeler Loan:\n✔️ Minimum age: 21 years\n✔️ Income proof required\n✔️ Valid Aadhaar & PAN\n✔️ Good repayment history preferred.",

    "two wheeler documents": "Documents required for Two-Wheeler Loan:\n📌 Aadhaar\n📌 PAN\n📌 Address proof\n📌 Bank statement\n📌 Income proof.",

    # Used Car Loan
    "used car loans": "🚗 Used Car Loan:\n-> Affordable interest rates\n-> Simple documentation\n-> Quick approval\n👉 [Apply Now](https://www.tvscredit.com/loans/used-car-loans)\n\nWhat would you like to do next? (Eligibility / Documents / Main Menu)",

    # Tractor Loan
    "tractor loans": "🚜 Tractor Loan:\n-> Customized repayment linked to crop cycles\n-> Low interest rates for farmers\n-> Quick processing\n👉 [Apply Now](https://www.tvscredit.com/loans/tractor-loans)\n\nWhat would you like to do next? (Eligibility / Documents / Main Menu)",

    # Other Loan Types (short)
    "personal loans": "💰 Personal Loans are available to meet urgent financial needs with flexible tenure.\n👉 [Apply Now](https://www.tvscredit.com/loans/personal-loans)",
    "consumer durable loans": "🛒 Consumer Durable Loans for laptops, mobiles, TVs & appliances.\n👉 [Apply Now](https://www.tvscredit.com/loans/consumer-durable-loans)",
    "gold loans": "🏆 Gold Loans with attractive rates and instant processing.\n👉 [Apply Now](https://www.tvscredit.com/loans/gold-loans)",
    "loan against property": "🏠 Loan Against Property at competitive rates.\n👉 [Apply Now](https://www.tvscredit.com/loans/loan-against-property)",

    # ---------------- Existing Customer Flow ----------------
    "existing customer": "How would you like to log in?\n- Agreement Number\n- Mobile Number",

    "agreement number": "Please share your agreement number 📑.",
    "mobile number": "Please enter your registered mobile number 📱.",

    # ---------------- Employee Flow ----------------
    "employee": "To log in, please enter your Employee ID.",

    # ---------------- Channel Partner Flow ----------------
    "channel partner": "Which amongst the following best describes you?\n- Existing Channel Partner\n- New Channel Partner",

    "existing channel partner": "To get started, please enter your Dealer ID.",
    "new channel partner": "Please visit [TVS Partner Portal](https://www.tvscredit.com) to register.",

    # ---------------- EMI & Payment ----------------
    "emi": "Your EMI is usually due on the 5th of every month. Pay via NetBanking, UPI, or the TVS Credit app.",
    "emi payment": "You can pay your EMI through NetBanking, UPI, TVS Credit app, or at partner payment centers.",
    "emi due": "To check your EMI due date, log in to the TVS Credit app or website under 'My Loans'.",
    "missed emi": "If you miss an EMI, late payment charges may apply. Please pay immediately to avoid penalties.",

    # ---------------- General Loan Info ----------------
    "eligibility": "Eligibility is based on income, credit history, and product type. Aadhaar and PAN are mandatory.",
    "documents": "Commonly required documents: Aadhaar, PAN, income proof, and bank statement.",
    "cibil": "A good CIBIL score improves your loan eligibility. However, we also provide loans to new-to-credit customers.",

    # ---------------- Repayment & Statements ----------------
    "repayment": "You can repay your loan via EMI through auto-debit, UPI, or online payment on our app.",
    "foreclosure": "You can foreclose your loan after a minimum lock-in period. Foreclosure charges may apply.",
    "statement": "Download your loan statement from the TVS Credit app or website.",
    "receipt": "Your payment receipts are available under 'My Loans' in the TVS Credit app.",

    # ---------------- Support ----------------
    "customer care": "📞 Call us at 1800-123-4567 or 📧 email support@tvscredit.com for assistance.",
    "branch": "Locate the nearest TVS Credit branch using our branch locator on the website.",
    "complaint": "You can raise complaints through the TVS Credit app, website, or customer care helpline.",

    # ---------------- App & Offers ----------------
    "app": "Download the TVS Credit Saathi app from Play Store/App Store to manage your loans, EMI, and payments.",
    "login": "Use your registered mobile number to log in to the TVS Credit Saathi app.",
    "offers": "You can view personalized offers and pre-approved loans in the TVS Credit app.",

    # ---------------- Reminders & Collections ----------------
    "reminder": "We send proactive EMI reminders via SMS, WhatsApp, and app notifications.",
    "collections": "Our AI-powered collections system ensures timely EMI reminders and easy repayment options.",

    # ---------------- General Info ----------------
    "about": "TVS Credit is a leading NBFC in India offering loans for Two-wheelers, Cars, Tractors, and Consumer Durables.",
    "services": "Our services include loan disbursal, EMI collection, customer support, and personalized offers.",
    "contact": "You can reach us via our customer care helpline 1800-123-4567 or support@tvscredit.com.",
    "whatsapp": "TVS Credit services are available on WhatsApp for EMI reminders and quick queries.",

    # ---------------- Navigation ----------------
    "main menu": "Returning to Main Menu...\n- New Customer\n- Existing Customer\n- Employee\n- Channel Partner",
    "end conversation": "🙏 Thank you for chatting with TIA+ 🤖. Have a great day!",
    "change language": "Currently I support English. More languages coming soon!"
}

# -----------------------------
# Get bot response
# -----------------------------
def get_bot_response(user_id, user_message):
    user_message_lower = user_message.lower()

    # 1. Check FAQ dataset first
    for keyword, answer in faq_data.items():
        if keyword in user_message_lower:
            return answer

    # 2. If Gemini is enabled, try AI response
    if use_gemini and model:
        past_conversation = conversation_memory.get(user_id, [])
        context_text = "\n".join([f"{x['role']}: {x['message']}" for x in past_conversation])

        prompt = f"""
        You are TIA+, an AI assistant for TVS Credit.
        Answer in simple, clear language.
        If question is about finance, loans, EMI, or TVS Credit services, answer it.
        If unrelated, politely say you can only answer finance/loan related queries.

        Conversation so far:
        {context_text}

        User just asked: {user_message}
        """

        try:
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print("⚠️ Gemini error:", e)
            return "Sorry, I'm having trouble connecting to AI service. Please ask about loans, EMI, or services."

    # 3. Fallback if no match
    return "I can help with TVS Credit loans, EMI, and customer services. Can you rephrase your query?"

# -----------------------------
# Routes
# -----------------------------
@app.route("/")
def home():
    return render_template("index.html")  # Make sure index.html is inside 'templates/' folder

@app.route("/chat", methods=["POST"])
def chat():
    user_id = request.remote_addr
    user_message = request.json.get("message", "")

    if user_id not in conversation_memory:
        conversation_memory[user_id] = []

    conversation_memory[user_id].append({"role": "user", "message": user_message})

    bot_reply = get_bot_response(user_id, user_message)

    conversation_memory[user_id].append({"role": "bot", "message": bot_reply})

    return jsonify({"reply": bot_reply})

# -----------------------------
# Run
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)

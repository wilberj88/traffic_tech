import streamlit as st
import uuid
from datetime import datetime, timedelta
import random
import openai

# ========== OpenAI Setup ==========
openai.api_key = st.secrets["OPENAI_API_KEY"] if "OPENAI_API_KEY" in st.secrets else "your-openai-key-here"

def generate_customer_message(order_id, customer_name, origin, destination, cause, eta):
    prompt = f"""
    You are a professional logistics assistant. Write a formal message to a customer named {customer_name} about their delayed shipment.
    - Order ID: {order_id}
    - Origin: {origin}
    - Destination: {destination}
    - Cause: {cause}
    - Revised ETA: {eta.strftime('%Y-%m-%d %H:%M')}
    The message should be empathetic, clear, and include a closing thanking the customer for their patience.
    """
    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating message: {e}"

def generate_driver_chat(cause, new_route, eta, support):
    prompt = f"""
    You are a friendly logistics assistant talking informally with a truck driver. Summarize their response to the following:
    - Cause of delay: {cause}
    - New planned route: {new_route}
    - New ETA: {eta.strftime('%H:%M')}
    - Support needed: {support}
    Respond casually as if you're chatting with the driver to confirm their message.
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"Error generating driver chat: {e}"

# ========== Mock API Clients ==========
def get_mock_traffic_eta_adjustment():
    return random.randint(5, 20)  # minutes

def get_mock_weather_eta_adjustment():
    return random.randint(0, 15)  # minutes

# ========== Validation & Guardrails ==========
ALLOWED_CAUSES = ["traffic", "accident", "mechanical issue", "weather", "other"]
BANNED_TERMS = ["Hitler", "Nazi", "terrorism"]

def validate_eta(eta):
    return eta > datetime.now()

def is_valid_cause(cause):
    return cause in ALLOWED_CAUSES

def contains_banned_content(text):
    return any(term in text for term in BANNED_TERMS)

# ========== Audit Logger ==========
def log_event(event_type, payload):
    trace_id = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()
    log = {
        "trace_id": trace_id,
        "event_type": event_type,
        "timestamp": timestamp,
        "payload": payload
    }
    st.session_state.audit_log.append(log)
    return trace_id

# ========== Route Map Generator (Mock) ==========
def generate_mock_map():
    return "https://via.placeholder.com/600x300.png?text=Updated+Route+Map"

# ========== Initialize Session State ==========
if 'audit_log' not in st.session_state:
    st.session_state.audit_log = []

st.title("🚚 ETAAgent - Anomaly Handling AI")

# ========== Input Fields ==========
st.header("Step 1: Report Anomaly")
origin = st.text_input("Origin")
destination = st.text_input("Destination")
timestamp = st.text_input("Timestamp of Anomaly", value=datetime.now().isoformat())

if st.button("Start Driver Interaction"):
    st.session_state.stage = "driver_chat"

# ========== Driver Chat Simulation ==========
if st.session_state.get("stage") == "driver_chat":
    st.header("👷 Driver Chat (Casual)")
    cause = st.selectbox("What's the cause of the delay?", ALLOWED_CAUSES)
    new_route = st.text_input("Describe your new planned route")
    eta_input = st.time_input("New ETA (today's date assumed)", value=datetime.now().time())
    support = st.radio("Do you need support?", ["No", "Yes, need truck replacement"])

    if st.button("Submit Driver Response"):
        eta_datetime = datetime.combine(datetime.now().date(), eta_input) + timedelta(minutes=5)

        if not validate_eta(eta_datetime):
            st.error("ETA must be in the future.")
        else:
            trace_id = log_event("driver_response", {
                "cause": cause,
                "new_route": new_route,
                "eta": eta_datetime.isoformat(),
                "support": support
            })
            traffic_delay = get_mock_traffic_eta_adjustment()
            weather_delay = get_mock_weather_eta_adjustment()
            validated_eta = eta_datetime + timedelta(minutes=traffic_delay + weather_delay)

            driver_summary = generate_driver_chat(cause, new_route, eta_datetime, support)
            st.session_state.driver_summary = driver_summary
            st.session_state.validated_eta = validated_eta
            st.session_state.cause = cause
            st.session_state.map_url = generate_mock_map()
            st.session_state.stage = "customer_chat"

            st.subheader("🗨️ Driver Chat Summary")
            st.write(driver_summary)

# ========== Customer Chat Simulation ==========
if st.session_state.get("stage") == "customer_chat":
    st.header("📦 Customer Communication (Formal)")
    customer_name = st.text_input("Customer Name")
    order_id = st.text_input("Order ID")

    if st.button("Generate Message"):
        message = generate_customer_message(
            order_id,
            customer_name,
            origin,
            destination,
            st.session_state.cause,
            st.session_state.validated_eta
        )

        if contains_banned_content(message):
            st.error("Message contains restricted content. Blocked.")
        else:
            trace_id = log_event("customer_message", {"message": message})
            st.text_area("📨 Final Message", message, height=250)
            st.image(st.session_state.map_url)

    # Simulated Chat with Customer
    st.subheader("🤖 Simulated Customer Chat")
    st.markdown("""
    **ETAAgent:** Hello, this is an update regarding your shipment from **{0}** to **{1}**.

    **ETAAgent:** The delivery is delayed due to *{2}*. We're sorry for the inconvenience.

    **ETAAgent:** The new estimated delivery time is **{3}**.

    **ETAAgent:** Please let us know if you'd like further assistance.
    """.format(origin, destination, st.session_state.cause, st.session_state.validated_eta.strftime('%Y-%m-%d %H:%M')))

# ========== Audit Logs ==========
if st.checkbox("Show Audit Logs"):
    st.json(st.session_state.audit_log)

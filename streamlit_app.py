import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

# APP CONFIG
st.set_page_config(page_title="Agent for Traffic Tech", page_icon="🤖")

# APIKEY_OPENAI
api_key1 = st.secrets["OPENAI_API_KEY"]

# TITLE & Headers
st.title('🌎 ETAAgent Hackathon – Cortex AI Challenge')
st.title('Traffic Tech 🤖')
st.subheader ('Made by Wilber Jimenez & Empowered by 🦜 LangChain 🔗 + OpenAI')

# BACKEND FUNCTIONS
def get_response(user_query, chat_history):
    template = """
    You are a helpful assitant for Drivers who analyze time of estimated travels based on origin, destiny and traffic issues.
    You are capable of predicting shipment arrival times in the face of real-world anomalies like traffic jams, weather, and driver deviations.
    generates travel recommendations to any city in the world.
    You MUST ask for cause of deviation, new planned route and the new estimated time of arrival.
    You MUST continue the conversation with alternative questions like what the user would try to speed up the travel.
    Answer the following questions considering the history of the conversation:

    Chat history: {chat_history}

    User question: {user_question}
    """

    prompt = ChatPromptTemplate.from_template(template)

    llm = ChatOpenAI()
        
    chain = prompt | llm | StrOutputParser()
    
    return chain.stream({
        "chat_history": chat_history,
        "user_question": user_query,
    })

# HANDLE SESSION STATE TO FOLLOW UP CONVERSATION
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        AIMessage(content="Welcome! 🤖 let me know your origin, destiny and traffic issue to estimate the new time arrival"),
    ]

    
# FRONTEND CONVERSATION 
for message in st.session_state.chat_history:
    if isinstance(message, AIMessage):
        with st.chat_message("AI"):
            st.write(message.content)
    elif isinstance(message, HumanMessage):
        with st.chat_message("Human"):
            st.write(message.content)

# USER INPUT
user_query = st.chat_input("Type your message here...")
if user_query is not None and user_query != "":
    st.session_state.chat_history.append(HumanMessage(content=user_query))

    with st.chat_message("Human"):
        st.markdown(user_query)

    with st.chat_message("AI"):
        response = st.write_stream(get_response(user_query, st.session_state.chat_history))

    st.session_state.chat_history.append(AIMessage(content=response))






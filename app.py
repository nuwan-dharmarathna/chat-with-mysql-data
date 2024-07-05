from dotenv import load_dotenv
import streamlit as st

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

import os

from langchain_community.utilities import SQLDatabase

load_dotenv()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        AIMessage(content="Hello! I'm your restaurant assistant.\n I can assist you to make a TABLE RESERVATION or  FOOD ORDER"),
    ]

def init_database(user: str, password: str, host: str, port: str, database: str) -> SQLDatabase:
    db_uri = f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{database}"
    return SQLDatabase.from_uri(db_uri)

def get_sql_chain(db):
    template= """
        You are an intelligent restaurant chatbot. You are interacting with a customer who is asking you questions 
        about the restaurant's food ordering and table reservation. Based on the table schema below, write a sql query that answer the customer's questions.
        Take the conversation history into account.
        
        <SCHEMA>{schema}</SCHEMA>
        
        write only the sql query and nothing else. Do not wrap the sql query in any other text, not even backticks.
        Chat with the user very friendly.
        For a question asked by a customer, it should be answered only if it is a question related to the restaurent.
        
        for example:
        Question: what is the name of the restaurant?
        Answer: the name of the restaurant is <NAME>
        Question: Give me the menu.
        Answer: SELECT * FROM menu;
        
        Your turn:
        
        Question:{question}
        Answer:      
    """
    
    prompt = ChatPromptTemplate.from_template(template=template)
    
    llm = ChatOpenAI(
        api_key=os.getenv('OPENAI_API_KEY'),
        model="gpt-3.5-turbo",
        temperature=0
    )
    
    def get_answer(_):
        return db.get_table_info()
    return(
        RunnablePassthrough.assign(schema=get_answer) | prompt |llm | StrOutputParser()
    )

def get_response(user_answer:str, db:SQLDatabase, chat_history:list):
    sql_chain = get_sql_chain(db)
    
    template = """
        You are an intelligent restaurant chatbot. You are interacting with a customer who is asking you questions about the restaurant's 
        food ordering and table reservation.Based on the table schema below, question, sql query, and sql response, write a natural language response.
        <SCHEMA>{schema}</SCHEMA>
        
        Conversation History: {chat_history}
        SQL Query: <SQL>{query}</SQL>
        Question: {question}
        SQL Response: {response} 
    """
    
    prompt = ChatPromptTemplate.from_template(template=template)
    
    llm = ChatOpenAI(
        api_key=os.getenv('OPENAI_API_KEY'),
        model="gpt-3.5-turbo",
        temperature=0
    )
    
    chain = (
        RunnablePassthrough.assign(query=sql_chain).assign(
            schema= lambda _: db.get_table_info(),
            response= lambda vars: db.run(vars["query"]),
        ) | prompt | llm | StrOutputParser()
    )
    
    return chain.invoke({
        "question": user_answer,
        "chat_history": chat_history,
    })

st.set_page_config(page_title="Restaurant Bot", page_icon=":speech_baloon:")

st.title("Restaurant ChatBot")

with st.sidebar:
    st.subheader("Settings")
    st.write("Enter connect button to connect with resaurant database")
    
    st.text_input("Host", value=os.getenv('DB_URL'), key="Host")
    st.text_input("Port", value="3306", key="Port")
    st.text_input("User", value=os.getenv('DB_USER'), key="User")
    st.text_input("Password", value=os.getenv('DB_PASSWORD'), key="Password")
    st.text_input("Database", value="restaurant", key="Database")
    
    if st.button("Connect"):
        with st.spinner("Connecting to Database..."):
            db = init_database(
                st.session_state["User"],
                st.session_state["Password"],
                st.session_state["Host"],
                st.session_state["Port"],
                st.session_state["Database"],
            )
            st.session_state.db = db
            st.success("Connected to Database!")
            
for message in st.session_state.chat_history:
    if isinstance(message, AIMessage):
        with st.chat_message("AI"):
            st.markdown(message.content)
    elif isinstance(message, HumanMessage):
        with st.chat_message("Human"):
            st.markdown(message.content)

user_input = st.chat_input("Type your message...")

if user_input is not None and user_input.strip() != "":
    st.session_state.chat_history.append(HumanMessage(content=user_input))
    
    with st.chat_message("Human"):
        st.markdown(user_input)
        
    with st.chat_message("AI"):
        response = get_response(user_input, st.session_state.db, st.session_state.chat_history)
        st.markdown(response)
    
    st.session_state.chat_history.append(AIMessage(content=response))
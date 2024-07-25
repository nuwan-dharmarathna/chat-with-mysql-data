import streamlit as st
from streamlit_chat import message as chat_msg

from langchain_community.utilities import SQLDatabase
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

from langchain_openai import ChatOpenAI

from langchain_core.messages import AIMessage, HumanMessage

import os
from dotenv import load_dotenv

load_dotenv()

#initialize database
def init_database(user: str, password: str, host: str, port: str, database: str) -> SQLDatabase:
    db_uri = f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{database}"
    return SQLDatabase.from_uri(db_uri)

def get_sql_chain(db):
    template ="""
        You are a data analyst at a company. You are interacting with a user who is asking you questions 
        about the company's database. Based on the table schema below, write a sql query that answer the user's questions.
        Take the conversation history into account.
        
        <SCHEMA>{schema}</SCHEMA>
        
        write only the sql query and nothing else. Do not wrap the sql query in any other text, not even backticks.
        Chat with the user very friendly.
        For a question asked by a customer, it should be answered only if it is a question related to the restaurent.
        
        for example:
        Question: what are the vehicles in the company?
        SQL query: SELECT * FROM vehicle
        
        Your turn:
        
        Question:{question}
        Answer:      
    """
    
    prompt = ChatPromptTemplate.from_template(template)
    
    llm = ChatOpenAI(
        api_key=os.getenv('OPENAI_API_KEY'),
        model="gpt-3.5-turbo",
        temperature=0
        )
    
    def get_shema(_):
        return db.get_table_info()
    
    return(
        RunnablePassthrough.assign(schema = get_shema) | prompt | llm | StrOutputParser()
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

def init_dashboard():
    st.set_page_config(page_title="Chat with mySQL", page_icon="💬", layout="wide")
    st.title("Chat with your mySQL Database ⌸")

    with st.sidebar:
        st.subheader("Settings ⚙️")
        st.write("This is a simple chat application using mysql. Connect to your database & start chatting.")
        
        st.text_input("Host", value="localhost", key="Host")
        st.text_input("Port", value="3306", key="Port")
        st.text_input("User", value="root", key="User")
        st.text_input("Password", type="password", key="Password")
        st.text_input("Database name", key="Database")
        
        if st.button("Connect to Database"):
            try:
                db = init_database(
                    st.session_state["User"],
                    st.session_state["Password"],
                    st.session_state["Host"],
                    st.session_state["Port"],
                    st.session_state["Database"]
                )
                st.session_state.db = db
                st.success(f"Connected to your Database ✅")
            except:
                st.warning(f"Database not connected!")
           
def main():
    # initialize dashboard
    init_dashboard()
    
    if "db" not in st.session_state or st.session_state.db is None:
        st.info("Connect your mySQL Database")
    
    else:
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = [
                AIMessage(content="Hello, I am a bot. How can I help you")
            ]


        user_query = st.chat_input("Enter your chat here...")

        if user_query is not None and user_query.strip() != "":
            with st.spinner("Thinking..."):
                response = get_response(user_query, st.session_state.db, st.session_state.chat_history)
            
            st.session_state.chat_history.append(HumanMessage(content=user_query))
            st.session_state.chat_history.append(AIMessage(content=response))
            
        for i, msg in enumerate(st.session_state.chat_history):
            if i % 2 != 0:
                chat_msg(msg.content, is_user=True, key=str(i)+'_usr')
            else:
                chat_msg(msg.content, is_user=False, key=str(i)+'_ai')

if __name__ == '__main__':
    main()
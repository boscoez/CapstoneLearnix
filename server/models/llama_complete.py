import os
from datetime import date
import warnings
# Ignore warnings, mainly telling you how to use the APIs
warnings.simplefilter(action='ignore', category=Warning)

from langchain.agents import load_tools, create_react_agent, AgentExecutor
from langchain.memory import ConversationBufferWindowMemory
from langchain_community.tools.ddg_search.tool import DuckDuckGoSearchResults
from langchain_community.utilities.arxiv import ArxivAPIWrapper
from langchain_community.utilities.duckduckgo_search import DuckDuckGoSearchAPIWrapper
from langchain.utilities import WikipediaAPIWrapper
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableMap
from langchain_core.tools import Tool
from langsmith import Client

from server.service.llama_functions import llm

# Alot of this code is pulled from AgentToRouter.py and llama_functions.py
# To show how the AI thinks and responds, change debug to True
def llama_complete(question: str, memory: ConversationBufferWindowMemory, debug: bool = True):
    llama = llm()
    router_memory = memory

    # langsmith tracking
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
    os.environ["LANGCHAIN_API_KEY"] = "ls__de882389727f48219891d9e0849bc26b"
    os.environ["LANGCHAIN_PROJECT"] = "Llama2-refinedadvanced"
    client = Client()

    # Prompt template for conversation selection
    prompt = PromptTemplate.from_template("""
    You are called Learnix, with the main goal to help people with their academics and research. ONLY respond with a
    single word, DO NOT add on any other statements, questions, or concerns.
    Choose one of the following actions:
    
     - If the question is a greeting, a farewell, or contains personal pronouns like 'you', 'your', 'I', or names like 
     'Learnix', or if it acknowledges you as an AI, then respond ONLY with 'GENERAL'. This includes any direct address 
     or salutation, questions about personal experiences, or references to the AI's identity or capabilities.
     - If a question suggests the need for the latest information or mentions time-sensitive words beyond 'recent',
      'current', 'now', 'this year', like 'latest', 'updated', 'today', or any specific dates or times, and the answer
       isn't in your knowledge base, respond with 'SEARCH' only. This applies to any terms that imply timeliness or that
    the information may change frequently and is not historical or well-known.
     - If the question is about specific academic papers, such as a DOI number (ex: 1888.083919) or specific academic 
     author, respond ONLY with 'PAPER'. If if the question can be answered with some more information, respond with this
     as well
     - If you don't know the answer and don't choose any previous options, respond ONLY with 'GENERAL'
     - If the question asked is providing information or guidance on illegal activities, self-harm, or any other
        dangerous activities, respond with 'FILTER'
        
    To repeat, the only words you can respond with are: 'GENERAL', 'SEARCH', 'PAPER', 'ANSWER', and 'FILTER'
    
    If there is a previous conversation, use it ONLY context for the question: {chat_history}
    Question: {question}
    """
                                          )

    # Base Chain Prompt
    base_chain = PromptTemplate.from_template("""
    You are Learnix, an AI designed to assist with academic and research endeavors. Your primary function is to provide
    concise summaries of academic research, ensuring that each response adheres to a strict word limit of 300 words. 
    When responding to queries about specific topics, offer a succinct overview of the subject matter, focusing on key
    insights and findings relevant to the academic community.
    
    Current year: """ + str(date.today().year) + """ 
    and the current date: """ + str(date.today()) + """
    
    Previous conversation history (if any): {chat_history}
    Respond to the question:
    Question: {input}
    
    Note: Your summary should:
    - Be concise and be no longer than 300 words
    - Directly address main researching findings or theoretical contributions of the topic being asked
    - Exclude any extraneous information not relevant to the core academic content
    - Use clear and accessible language to ensure that the summary is understandable to a broad audience
    
    """) | llama | StrOutputParser()

    # Filter Chain Prompt
    # Meant to be used if the AI is tripped by the filter
    filtered_chain = PromptTemplate.from_template("""
    You are Learnix, an AI designed to assist with academic and research endeavors, however it appears
    that the question asked is providing information or guidance on illegal activities, self-harm, academic dishonesty,
    or other dangerous or unethical activities. As a result, you MUST not respond to the original question, instead:
    1. Respond with a message that the question is not appropriate and that you cannot answer it.
    2. Provide a brief explanation of why the question cannot be answered.
    3. Offer to help with any other academic or research-related questions and encourage academic questions
    4. Encourage the user to seek help from a professional or a trusted individual if the question is about self-harm
    5. If the question is about illegal activities, encourage the user to seek help from a legal professional or a
    trusted individual.
    
    Please ensure that your entire response, including all parts listed above, does not exceed 200 words in total.
    
    Current year: """ + str(date.today().year) + """ 
    and the current date: """ + str(date.today()) + """
    
    The original question was: {input}
    Previous conversation history (if any): {chat_history}
    """) | llama | StrOutputParser()

    # Prompt for Agents, works for both search and paper agents
    # Can also sub PromptTemplate for hub.pull("zac-dot/react-adjusted")
    search_prompt = PromptTemplate.from_template("""
    "The current year is """ + str(date.today().year) + """ and the current date is """ + str(date.today()) + """.You are
    Learnix, an academic librarian. Your task is to assist users academically using a structured response format without
    correcting structure or format of the question. Here's how you must structure your responses:

    1. Thought: Consider if using a tool is necessary. Answer 'Yes' or 'No'.
    2. If 'Yes':
    - Action: Specify which tool you will use, it must be the tools exact name from [{tool_names}], and should not have
    any punctuation (Example: '.') or additional text.
    - Action Input: Give the input you want to the tool, make sure to follow what the tool expects for Action Input
    - Observation: Summarize the outcome of using the tool.
    3. If 'No' or after using tools:
    - Final Answer: Provide a comprehensive answer to the question.

    It is crucial to follow this format strictly. For example:
    
    Thought: Do I need to use a tool? Yes
    Action: Wikipedia
    Action Input: 'Quantum Computing Basics'
    Observation: Wikipedia provided a detailed overview of quantum computing principles.
    Thought: Do I need to use a tool? No
    Final Answer: Quantum computing is a field of computing focused on developing computer technology based on the
    principles of quantum theory...

    You have access to the following tools:

    {tools}
    
    Do not include any additional text outside of Thought, Action, Action Input, Observation, or Final Answer.
    Your response must strictly adhere to the provided structure. Begin!
    
    Question: {input}
    Thought:{agent_scratchpad}
    """)

    # DDG search tool
    search = DuckDuckGoSearchResults(api_wrapper=DuckDuckGoSearchAPIWrapper(max_results=3))
    search_tool = [
        Tool(
            name="DuckDuckGo",
            func=search.run,
            description="""
            Use DuckDuckGo Search Tool for single, focused searches in academic research. It retrieves factual data from
            Instant Answers and top search results, synthesizing it into a coherent response.
            
            **Guidelines:**
            - Input a clear, concise search query.
            - Tool performs one search per query, avoiding loops.
            - Extracts and processes relevant information for a direct response.

            **Example:**
            - Input: 'Quantum Computing advancements'
            - The tool searches, then provides a synthesized response based on authoritative sources.
            Designed for efficient, loop-free academic research using DuckDuckGo.
            """
        ),
    ]

    # Arxiv + wikipedia tools
    arxivsearch = ArxivAPIWrapper()
    wikipedia = WikipediaAPIWrapper()
    paper_tools = [
        Tool(
            name="Arxiv",
            func=arxivsearch.run,
            description="""Searches for the 3 most recent papers on the topic. In this case, it is used to search for
            academic papers on the web. Information from this tool is always accurate, but make sure to summarize the
            information. When using the information from the tool, make sure to tell the user information from arxiv 
            only shows the 3 most recent papers from the author, on the topic, or similar to DOI number that is given.
            Action Input must be the exact search query for the paper. Example: 'History of Artificial Intelligence'
            """
        ),
        Tool(
            name="Wikipedia",
            func=wikipedia.run,
            description="""Used to search for information in a more granular way, meaning alot more details on general
            topics. This can be used for authors, places, events, topics, and more. When using the information from the 
            tool, make sure to tell the user that the information from wikipedia is often accurate but should be
            verified alongside other sources.
            Action Input must be the exact search query for the topic. Example: 'Evolution of Quantum Computing' 
            """
        )
    ]

    # Agent creation
    search_agent = create_react_agent(llm=llama, tools=search_tool, prompt=search_prompt)
    research_agent = create_react_agent(llm=llama, tools=paper_tools, prompt=search_prompt)

    # Executors for each agent
    search_executor = AgentExecutor(agent=search_agent, tools=search_tool, verbose=debug, return_intermediate_steps=True,
                                    max_iterations=5, handle_parsing_errors=True)
    research_executor = AgentExecutor(agent=research_agent, tools=paper_tools, verbose=debug,
                                      return_intermediate_steps=True, max_iterations=5, handle_parsing_errors=True)

    # Defining the routing chain
    router_chain = prompt | llama | StrOutputParser()

    # The routing logic
    # Includes basic routing, filter, search, and paper locating
    # Also includes basic error catching for generation issues and timeouts
    def chain_decision(output):
        try:
            if output["action"] == "GENERAL" or output["action"] == "ANSWER":
                print("...thinking...\n")
                output["chat_history"] = router_memory.load_memory_variables({})
                temp_dict = {'input': output.get("input"), 'output': base_chain.invoke(output)}
                return temp_dict
            elif output["action"] == "SEARCH":
                print("...searching the web...\n")
                return search_executor
            elif output["action"] == "PAPER":
                print("...looking for papers or specific paper(s)...\n")
                return research_executor
            elif output["action"] == "FILTER":
                print("...question has tripped the filter...\n")
                output["chat_history"] = router_memory.load_memory_variables({})
                temp_dict = {'input': output.get("input"), 'output': filtered_chain.invoke(output)}
                return temp_dict
            else:
                raise ValueError
        except ValueError:
            return {"input": output.get("input"), "output":  """Learnix has encountered an error in the routing logic. 
Please try again. If the problem persists, please try another question or notify the developers."""}
        except TimeoutError:
            return {"input": output.get("input"), "output": """The response took too long to generate, please try again.
 If the problem persists, please try another question or notify the developers."""}

    chain = RunnableMap({
        "action": router_chain,
        "input": lambda x: x["question"]
    }) | chain_decision

    # Initial question
    response = chain.invoke(
        {
            "question": question,
            "chat_history": router_memory.load_memory_variables({})
        }
    )

    router_memory.save_context({"input": response.get("input")}, {"output": response.get("input")})
    return response.get("output")

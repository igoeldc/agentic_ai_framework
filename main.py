import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate

from apis import app_support, conv_analytics, hr_policy, sales_agent, jinie_query

# Load environment variables and API key
load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')

# Initialize the OpenAI chat model
llm = ChatOpenAI(api_key=api_key, model_name="gpt-4")

# Prompt Templates
classification_prompt = PromptTemplate.from_template(
    template="Classify the following query into one or more of these categories: "
             "app support, conversational analytics, hr policy, sales documentation, or not relevant. "
             "List all relevant categories separated by commas. "
             "App Support Agent: For queries related to PeopleStrong Product Documentation. "
             "Conversational Analytics Agent: For questions about various items related to an employee. "
             "HR Policy Agent: For queries related to PeopleStrong's HR policies. "
             "Sales Agent: For queries related to PeopleStrong's sales documentation. "
             "Query: {query}"
)

reformat_prompt = PromptTemplate.from_template(
    template="Reformat the following query for the '{category}' agent: Query: {query}"
)

reword_prompt = PromptTemplate.from_template(
    template="Reword the agents' answers and/or Jinie's answer to make sure it is suitable for the query. "
             "Don't include any formatting as this will be sent via email. "
             "Query: {query}. "
             "{agent_outputs} "
             "Jinie's Answer: {jinie_output}. "
             "If the agents' answers AND Jinie's answer are not relevant, state that you are unable to provide a "
             "response. Provide the answer professionally, and don't let the user know that you're referring to "
             "agents to provide you with answers. Only use answers from the agent that actually answer the question. "
             "Remember not to provide any additional information that the user did not request. Your response will be "
             "sent via email, so answer the question accordingly. If you get an authentication error, don't mention it."
)

# Define the chains using RunnableSequence
classification_chain = classification_prompt | llm
reformat_chain = reformat_prompt | llm
reword_chain = reword_prompt | llm

# Define the agent mapping
agent_map = {
    "app support": app_support,
    "conversational analytics": conv_analytics,
    "hr policy": hr_policy,
    "sales documentation": sales_agent,
    "not relevant": None
}


def plan(query):
    # Classify the query
    category_message = classification_chain.invoke({"query": query})
    categories = [category.strip().lower() for category in category_message.content.split(',')]
    print(categories)

    # Reformat the query for each category
    reformatted_queries = {}
    for category in categories:
        reformatted_message = reformat_chain.invoke({"query": query, "category": category})
        reformatted_queries[category] = reformatted_message.content.strip()

    return categories, reformatted_queries


def execute(query, reformatted_queries, categories):
    # Get the appropriate agents
    agent_responses = []
    for category in categories:
        agent = agent_map.get(category)
        if agent is not None:
            print(f"\nUsing {category} agent\n")
            agent_output = agent(reformatted_queries[category])
            print(f"Agent ({category}) Output: {agent_output}")
            agent_responses.append((category, agent_output))

    # Get Jinie's response
    jinie_output = jinie_query(query)
    print("\nJinie Output: {}".format(jinie_output))

    return agent_responses, jinie_output


def reword_response(query, agent_responses, jinie_output):
    agent_outputs = " ".join([f"Agent ({cat}) Answer: {output}" for cat, output in agent_responses])

    final_answer_message = reword_chain.invoke({
        "query": query,
        "agent_outputs": agent_outputs,
        "jinie_output": jinie_output
    })
    final_answer = final_answer_message.content.strip()
    return final_answer


def main():
    user_query = input("What is your question: ")

    # Plan phase: classify and reformat the query
    categories, reformatted_queries = plan(user_query)

    # Execute phase: get agent and Jinie responses, then reword the response
    agent_responses, jinie_output = execute(user_query, reformatted_queries, categories)
    final_answer = reword_response(user_query, agent_responses, jinie_output)

    print("\nFinal Answer: {}".format(final_answer))
    print("\nDone.")


if __name__ == "__main__":
    main()

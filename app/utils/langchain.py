
# This is a good link. There's a lot going on with agents and tool use
# https://python.langchain.com/docs/use_cases/tool_use/prompting/
# This is using tool calling (like with gemini)
# https://python.langchain.com/docs/modules/agents/agent_types/tool_calling/
# Tools are best made when decorated and annotated following this guide:
# https://python.langchain.com/docs/modules/tools/custom_tools/
# And this is how to do it without giving the model the ability to use tools
# https://python.langchain.com/docs/use_cases/tool_use/prompting/
# It is done via structured output using a parser, where the model basically describes what it wants to do.

# The generic VertexAI model integration, uses GCP enterprise costs, not it's API key version like OpenAI.
# https://python.langchain.com/docs/integrations/chat/google_vertex_ai_palm/

from langchain_core.prompts import ChatPromptTemplate
# ChatPromptTemplate works better for models which expect roles, like OpenAI. Otherwise, use PromptTemplate
from langchain.prompts import PromptTemplate
from langchain_google_vertexai import ChatVertexAI
from langchain.agents import AgentExecutor, create_tool_calling_agent

from .langchain_tools import get_known_workout_names_tool, create_workout_recommendation_tool, get_past_5_workouts_tool

# Debugging
from langchain.globals import set_debug
from langchain.globals import set_verbose

set_debug(True)
set_verbose(True)

import vertexai

# Needed since in a container, and the project isn't set through just credentials
vertexai.init(project="practice-project-thorin", location="europe-west2")

# from .utils.langchain_tools import get_known_workout_names_tool, create_workout_recommendation_tool

def simple_prompt(
    user_query,
    user_id,
):
    """
    
    Things learnt:

    Giving an LLM steps to follow is a good way of making it likely that tools are called.

    When tools are involved, keep temperature at 0. You want to be sure that the model is always using your
    tool, and not just because it was not crystal clear and it choose to use the tool.

    Tools don't necessarily need to be explained, instead describing how and when the LLM should use them.

    IndexErrors can be due to a number of reasons. Such as blocked responses. Though I have found that it can be
    unexpected results from tools. Sometimes tools through errors, which the chain can detect, but returning a value
    to indicate failure can result in the AI just getting stuck. Eg '404: Exercise not available'.

    """

    # TODO -> Limit number of tokens in user input
    # TODO -> Combine known workouts and user workouts into one step?

    print(user_query)

    system_msg = f"""
    You are a helpful assistant who gives workout recommendations. The workouts recommended should target the muscle groups that the user specifies, if any.

    user_id = "{user_id}"
    
    Follow these steps exactly:

    1. Use the get_past_5_workouts_tool tool to get the user's latest completed workouts, newest first. use this to get some context on the user's ability, such as the exercises, weights, and reps that they've used before.
    2. Get a list of exercise names using the get_known_workout_names_tool tool.
    3. Selecting only from the list of names in step 2, select the most suitable exercises for this recommendation. 5 or 6 names is a good number unless more are requested.
    4. Using the names selected in step 2, create a JSON following this format:

    [
        {{{{
            "exercise_name" : ...,
            "reps" : ..., 
            "weight": ...,
            "position": ...,
            "units": ..., 'kg' or 'lbs'
        }}}}
    ]

    4. Pass the JSON from step 3 to the create_workout_recommendation_tool tool.

    """

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                system_msg
            ),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ]
    )


    # Add user_id to the function call, and don't rely on LLM needing it?
    tools = [
        get_known_workout_names_tool,
        create_workout_recommendation_tool,
        get_past_5_workouts_tool,
    ]

    for i, tool in enumerate(tools):
        print(f"Tool {i+1}")
        print(tool.name)
        print(tool.description)
        print(tool.args)

    # https://cloud.google.com/python/docs/reference/aiplatform/latest/vertexai.generative_models.GenerativeModel
    # https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/gemini
    # https://cloud.google.com/vertex-ai/generative-ai/docs/learn/model-versioning#gemini-model-versions

    # See parameters available, like temperature

    # IMPORTANT: Always specify a specific version where possible. Different model versions may expect different prompt
    # templates.
    llm = ChatVertexAI(
        model_name="gemini-1.5-flash", # New as of 9th April 2024. Supports system messages now
        convert_system_message_to_human=False,
        max_retries=1,
        request_parallelism=1,
        temperature=0.0,
        # max_output_tokens=2000,
    )

    agent = create_tool_calling_agent(llm, tools, prompt)

    # Note the verbose here
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    # Seems to struggle in "day" is used, instead of workout
    agent_output = agent_executor.invoke(
        {
            # "input" : f"What would you suggest for a leg workout?",
            # "input" : f"What would you suggest for an arm workout?",
            # "input" : f"What would you suggest for arm day?",
            # "input" : f"What workout would you suggest for arm day?",
            # "input" : f"Can you suggest a workout of 6-8 exercises that targets my chest please?",
            # "input" : f"No additional user input",
            "input" : user_query,
        },
    )

    print(agent_output)

    # chain = prompt | llm
    # https://api.python.langchain.com/en/latest/messages/langchain_core.messages.ai.AIMessage.html
    # chain_output = chain.invoke(
    #     {
    #         "input" : "What would you suggest for arm day?",
    #     },
    # )
    # print("Recommendation:")
    # print(chain_output.content)

    return agent_output["output"]

# https://python.langchain.com/docs/use_cases/tool_use/quickstart/

# A generic tool calling setup, which works as long as the model supports tool calling, like gemini
# https://python.langchain.com/docs/modules/agents/agent_types/tool_calling/

# def 

# Chains are hard coded sequences. Agents in LangChain choose which chains/actions to perform and in which order.
"""
In this advanced Interactive Workflows example, a pair of flows works together
to create an interactive chatbot.

This example uses Marvin, a toolkit for building natural language interfaces,
to talk to OpenAI's API. Follow the setup instructions in the Marvin docs to
make sure your OpenAI API key is set up correctly:

    https://www.askmarvin.ai/welcome/tutorial/#getting-an-openai-api-key

As with other examples, you should also be set up with Prefect Cloud or
a running open-source Prefect server.
    
After setup is comlete, you can try this example by opening two terminals.
Both should have access to the Python environment where you've installed
Prefect and Marvin. In one terminal, run the "answerer" flow:

    $ python llm_chatbot.py answerer
    
In another terminal, run the "chat" flow:

    $ python llm_chatbot.py chat
    
The "chat" flow will prompt you for a question, and the "answerer" flow will
use GPT to answer your question. The "chat" flow will then display the answer.
To get a sense of what's possible, note a few of the details:

- The chat flow starts a flow run of the answerer flow to use as its backend
    and then keeps track of the state of the flow run on every iteration of the
    loop. 

- The answerer expects to continually process questions and return
    responses, so most of its activity happens inside of a loop that checks
    for new questions on every iteration.

- The chat flow similarly expects to keep looping and getting questions,
    submitting them, and displaying the results.

- Because the answerer expects to suspend and resume, it needs to store
    a reference to questions it has already answered, so it can ignore them
    when it replays all the questions after resuming. We use a JSON Block
    for this. This allows the flow to suspend itself and resume where it
    left off, which it does relatively quickly, after one minute without
    receiving a question.

- However, the chat flow does not expect to suspend itself, so it does not
    need to store answered question keys in a JSON Block. However, it still
    needs to keep track of which answers it has already received. It does
    this transparently by using the iterator returned by `receive_input`
    to ask for the next answer on every iteration of the loop.
"""

import asyncio
import sys
from uuid import uuid4

from prefect import flow
from prefect.blocks.system import JSON
from prefect.client import get_client
from prefect.context import get_run_context
from prefect.deployments.deployments import run_deployment
from prefect.engine import resume_flow_run, suspend_flow_run
from prefect.input.run_input import receive_input, send_input
from prefect.logging.loggers import get_run_logger

from marvin.beta.assistants import Assistant


@flow(log_prints=True)
async def question_answerer():
    logger = get_run_logger()
    run_context = get_run_context()

    instructions = """
        You are Uncle Joe, a retired New York City cab driver with multiple PHDs
        in psychology and comparative religion. You dispense life advice in 
        short, quippy answers. You're speaking to your niece or nephew.
    """

    assert run_context.flow_run, "Could not see my flow run ID"
    block_name = f"{run_context.flow_run.id}-seen-ids"

    try:
        seen_ids_block = await JSON.load(block_name)
    except ValueError:
        seen_ids_block = JSON(
            value={"seen_question_keys": []},
        )

    with Assistant(
        name="Uncle Joe",
        instructions=instructions,
    ) as ai:
        try:
            logger.info("Receiving questions, seen keys: %s", seen_ids_block.value)
            async for question in receive_input(
                str,
                poll_interval=1,
                timeout=60,
                exclude_keys=seen_ids_block.value["seen_question_keys"],
                raise_timeout_error=True,
                with_metadata=True,
            ):
                try:
                    response_messages = await ai.say_async(question.value)

                    for answer in response_messages:
                        message_text = ""
                        for message in answer.content:
                            text_answer = message.text.value
                            message_text += f"\n\n{text_answer}"
                        await question.respond(message_text)
                        logger.info("answered: %s", message_text)
                except Exception as exc:
                    logger.exception("Error answering question: %s", exc)
                else:
                    seen_ids_block.value["seen_question_keys"].append(
                        question.metadata.key
                    )
                    logger.info("Saving JSON block: %s", seen_ids_block.value)
                    await seen_ids_block.save(name=block_name, overwrite=True)
        except TimeoutError:
            logger.info("Answerer timed out. Suspending flow run.")
            await suspend_flow_run(key=str(uuid4()), timeout=99999)


@flow
async def chat_session():
    # Start a question answerer flow run via deployment. Ideally, we would look
    # for a running instance and use it rather than always starting a new one
    # each run.
    flow_run = await run_deployment(
        "question-answerer/question-answerer", timeout=0, as_subflow=False
    )
    answers = receive_input(
        str,
        poll_interval=0.1,
        timeout=3,
        raise_timeout_error=True,
    )
    client = get_client()
    last_receive_timed_out = False
    question = ""
    progress = "..."

    while True:
        if not last_receive_timed_out:
            question = input("Ask a question: ")
            if not question:
                continue

        lower_q = question.lower()

        if lower_q.strip() in ("quit", "bye", "q", "stop", "break"):
            print("Ending chat session")
            break

        flow_run = await client.read_flow_run(flow_run.id)

        if not flow_run.state:
            continue
        if flow_run.state.is_paused():
            print("Chat is suspended. Resuming now...")
            await resume_flow_run(flow_run.id)
        elif flow_run.state.is_failed() or flow_run.state.is_crashed():
            print("Chat session encountered an error. Restarting chat.")
            flow_run = await run_deployment(
                "question-answerer/question-answerer", timeout=0, as_subflow=False
            )
        elif flow_run.state.is_completed():
            print("Chat session completed.")
            break

        if not last_receive_timed_out:
            await send_input(question, flow_run.id)

        last_receive_timed_out = False

        print(f"\rWaiting for answer{progress}", end="", flush=True)
        try:
            progress = "..."
            answer = await answers.next()
            print(f"\nAnswer: {answer}\n")
        except TimeoutError:
            progress += "."
            last_receive_timed_out = True

    print("Chat session ended")


if __name__ == "__main__":
    if sys.argv[1] == "answerer":
        asyncio.run(question_answerer.serve(name="question-answerer"))
    elif sys.argv[1] == "chat":
        asyncio.run(chat_session())

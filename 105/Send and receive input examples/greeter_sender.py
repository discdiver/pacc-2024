import asyncio
import sys
from prefect import flow, get_client
from prefect.blocks.system import JSON
from prefect.context import get_run_context
from prefect.deployments.deployments import run_deployment
from prefect.input.run_input import receive_input, send_input


EXIT_SIGNAL = "__EXIT__"


@flow
async def greeter():
    run_context = get_run_context()
    assert run_context.flow_run, "Could not see my flow run ID"

    block_name = f"{run_context.flow_run.id}-seen-ids"

    try:
        seen_keys_block = await JSON.load(block_name)
    except ValueError:
        seen_keys_block = JSON(
            value=[],
        )

    async for name_input in receive_input(
        str, with_metadata=True, poll_interval=0.1, timeout=None
    ):
        if name_input.value == EXIT_SIGNAL:
            print("Goodbye!")
            return
        await name_input.respond(f"Hello, {name_input.value}!")

        seen_keys_block.value.append(name_input.metadata.key)
        await seen_keys_block.save(name=block_name, overwrite=True)


@flow
async def sender():
    greeter_flow_run = await run_deployment(
        "greeter/send-receive", timeout=0, as_subflow=False
    )
    receiver = receive_input(str, timeout=None, poll_interval=0.1)
    client = get_client()

    while True:
        flow_run = await client.read_flow_run(greeter_flow_run.id)

        if not flow_run.state or not flow_run.state.is_running():
            continue

        name = input("What is your name? ")
        if not name:
            continue

        if name == "q" or name == "quit":
            await send_input(EXIT_SIGNAL, flow_run_id=greeter_flow_run.id)
            print("Goodbye!")
            break

        await send_input(name, flow_run_id=greeter_flow_run.id)
        greeting = await receiver.next()
        print(greeting)


if __name__ == "__main__":
    if sys.argv[1] == "greeter":
        asyncio.run(greeter.serve(name="send-receive"))
    elif sys.argv[1] == "sender":
        asyncio.run(sender())

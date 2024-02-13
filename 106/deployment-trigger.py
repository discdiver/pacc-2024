from prefect import flow
from prefect.events.schemas import DeploymentTrigger


@flow(log_prints=True)
def downstream_flow(prev_result: str) -> str:
    print(f"got {prev_result}")


downstream_deployment_trigger = DeploymentTrigger(
    name="Upstream Flow - Sell",
    enabled=True,
    match_related={"prefect.resource.id": "prefect.flow."},
    expect={"prefect.result.produced"},
    # parameters={
    #     "prev_result": "{{event.payload.result}}",
    # },
)


# expect is the main argument of the trigger object,
# this matches the event name of our emitted event

# match the flow id of the upstream flow

# here we take the flow id from the emitted event's payload
# and apply it to the flows parameter

if __name__ == "__main__":
    downstream_flow.from_source(
        source="https://github.com/discdiver/pacc-2024.git",
        entrypoint="102/weather2-tasks.py:pipeline",
    ).deploy(
        name="flow-with-weather-trigger",
        work_pool_name="managed1",
        triggers=[downstream_deployment_trigger],
    )

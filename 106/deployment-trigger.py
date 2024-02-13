from prefect import flow
from prefect.events.schemas import DeploymentTrigger


@flow(log_prints=True)
def downstream_flow(ticker: str) -> str:
    print(f"got {ticker}")


downstream_deployment_trigger = DeploymentTrigger(
    name="Upstream Flow - Sell",
    enabled=True,
    match={"prefect.resource.id": "prefect.flow.5c933ae4-dd43-4705-90eb-cfdeb4c028fb"},
)


# expect is the main argument of the trigger object,
# this matches the event name of our emitted event

# match the flow id of the upstream flow

# here we take the flow id from the emitted event's payload
# and apply it to the flows parameter

if __name__ == "__main__":
    downstream_flow.from_source(
        source="https://github.com/discdiver/pacc-2024.git",
        entrypoint="106/deployment-trigger.py:downstream_flow",
    ).deploy(
        name="ticker-deploy",
        work_pool_name="managed1",
        triggers=[downstream_deployment_trigger],
    )

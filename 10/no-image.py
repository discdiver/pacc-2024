from prefect import flow
from prefect import deploy


@flow(log_prints=True)
def local_flow():
    print("I'm a locally defined flow!")


if __name__ == "__main__":
    deploy(
        flow.from_source(
            source="https://github.com/desertaxle/demo.git",
            entrypoint="flow.py:my_flow",
        ).to_deployment(
            name="prefect-managed",
        ),
        work_pool_name="",
    )

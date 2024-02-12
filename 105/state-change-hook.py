from prefect import flow


def my_success_hook(flow, flow_run, state):
    print(f"Flow run {flow_run.id} succeeded!")


@flow(on_completion=[my_success_hook])
def my_flow():
    return 42


if __name__ == "__main__":
    my_flow()

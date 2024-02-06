from prefect import flow, deploy


@flow(log_prints=True)
def hi():
    print("hello")


if __name__ == "__main__":
    dep1 = hi.to_deployment(name="yo", work_pool="dock1")
    dep2 = hi.to_deployment(name="hey", work_pool="dock2")

    deploy(
        dep1,
        dep2,
        image="discdiver/two-pools:alpha",
        push=False,
        work_pool_name=None,
    )

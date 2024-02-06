from prefect import flow


@flow(log_prints=True)
def buy():
    print("Buying securities")


if __name__ == "__main__":
    buy.deploy(
        name="my-code-not-into-an-image-deployment2",
        work_pool_name="my-docker-pool",
        image="discdiver/no-build-image:1.0",
        build=False,
    )

import httpx
from prefect import flow, task


@task(retries=4, retry_delay_seconds=0.5)  # or [0.1, 0.5, 1, 2])
def fetch_random_code():
    random_code = httpx.get("https://httpstat.us/Random/200,500", verify=False)
    if random_code.status_code >= 400:
        raise Exception()
    print(random_code.text)


@flow
def fetch():
    fetch_random_code()


if __name__ == "__main__":
    fetch()

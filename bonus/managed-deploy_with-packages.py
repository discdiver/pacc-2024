from prefect import flow

if __name__ == "__main__":
    flow.from_source(
        "https://github.com/discdiver/prefect-examples.git",
        entrypoint="flows/hello_pandas.py:my_table_flow",
    ).deploy(
        name="test-imports",
        work_pool_name="prefect-managed",
        job_variables=dict(env=dict(EXTRA_PIP_PACKAGES="pandas")),
    )

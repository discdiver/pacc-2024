from prefect.deployments import run_deployment

run_deployment(
    name="pipeline/my-first-managed-deployment", parameters={"lat": 1, "lon": 2}
)

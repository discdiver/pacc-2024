from prefect import flow
from prefect.input.run_input import receive_input


@flow
def greeter_flow():
    for name_input in receive_input(str, timeout=None):
        # Prints "Hello, andrew!" if another flow sent "andrew"
        print(f"Hello, {name_input}!")


if __name__ == "__main__":
    greeter_flow()

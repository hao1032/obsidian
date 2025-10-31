import json

count = 0

def main_handler(event, context):
    print("Received event: " + json.dumps(event, indent=2))
    print("Received context: " + str(context))
    print("Hello world")
    return "Hello World" + str(count)


if __name__ == "__main__":
    a = main_handler({}, {})
    print(a)
    count = 5

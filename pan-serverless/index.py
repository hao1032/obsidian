import json

def main_handler(event, context):
    print("Received event: " + json.dumps(event, indent=2))
    print("Received context: " + str(context))
    print("Hello world")
    return "Hello World"


if __name__ == "__main__":
    event = {
        "body": "",
        "headers": {
            "accept": "*/*",
            "user-agent": "curl/8.4.0",
            "x-scf-request-id": "5948acff-b67d-11f0-843f-52540024e413"
        },
        "httpMethod": "GET",
        "path": "/",
        "queryString": {},
        "headerParameters": {},
        "isBase64Encoded": False,
        "pathParameters": {},
        "queryStringParameters": {},
        "requestContext": {
            "sourceIp": "36.159.237.104"
        }
    }

    context = {'memory_limit_in_mb': 128, 'time_limit_in_ms': 3000,
               'request_id': '5948acff-b67d-11f0-843f-52540024e413',
               'environment': '{"SCF_NAMESPACE":"default","TZ":"Asia/Shanghai"}',
               'environ': 'SCF_NAMESPACE=default;TZ=Asia/Shanghai', 'function_version': '$LATEST',
               'function_name': 'pan', 'namespace': 'default', 'tencentcloud_region': 'ap-guangzhou',
               'tencentcloud_appid': '1251467080', 'tencentcloud_uin': '543809431'}
    main_handler(event, context)

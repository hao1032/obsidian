# 请求

```shell
curl "https://lbepan.luoboedu.com?path=/"
```

# 网盘接口文档
https://pan.baidu.com/union/doc/nksg0sat9

# 参数解释说明
https://cloud.tencent.com/document/product/583/9210#.E6.89.A7.E8.A1.8C.E6.96.B9.E6.B3.95

# GET
```
event: {
  "body": "",
  "headers": {
    "accept": "*/*",
    "user-agent": "curl/8.4.0",
    "x-scf-request-id": "5d672784-b680-11f0-b5d6-5254005cb48d"
  },
  "httpMethod": "GET",
  "path": "/",
  "queryString": {
    "age": "30",
    "city": "New York",
    "name": "John"
  },
  "headerParameters": {},
  "isBase64Encoded": false,
  "pathParameters": {},
  "queryStringParameters": {},
  "requestContext": {
    "sourceIp": "36.159.237.104"
  }
}

context: {
  "memory_limit_in_mb": 128,
  "time_limit_in_ms": 3000,
  "request_id": "2891dd4f-4c21-4605-ad80-0fbe89edc1bf",
  "environment": "{\"SCF_NAMESPACE\":\"default\",\"TZ\":\"Asia/Shanghai\"}",
  "environ": "SCF_NAMESPACE=default;TZ=Asia/Shanghai",
  "function_version": "$LATEST",
  "function_name": "pan",
  "namespace": "default",
  "tencentcloud_region": "ap-guangzhou",
  "tencentcloud_appid": "1251467080",
  "tencentcloud_uin": "543809431"
}
```
# POST
```
event: {
  "body": "{\"name\": \"John\", \"age\": 30, \"city\": \"New York\"}",
  "headers": {
    "accept": "*/*",
    "content-length": "47",
    "content-type": "application/x-www-form-urlencoded",
    "user-agent": "curl/8.4.0",
    "x-scf-request-id": "c3b3a3e4-b67f-11f0-9795-525400d4c756"
  },
  "httpMethod": "POST",
  "path": "/tango",
  "queryString": {},
  "headerParameters": {},
  "isBase64Encoded": false,
  "pathParameters": {},
  "queryStringParameters": {},
  "requestContext": {
    "sourceIp": "36.159.237.104"
  }
}
```
# Port scan service

### Start

```docker-compose up```

### View

##### Sample input
```http://localhost/api/v1/query_port?ip=www.google.com&port=22,23,80,443```

##### Sample result

```
{
  "ip": "www.google.com", 
  "ports": {
    "22": false, 
    "23": false, 
    "80": true, 
    "443": true
  }
}
```

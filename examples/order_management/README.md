# Order management microservices example

## Run

You can spin up all the services with docker compose.

```bash
docker-compose up -d
```

## Tests

### Demo data

There are already some demo data loaded up on user and order service.
Find them in the `demo_data.py` file.

Login -

```bash
curl -X POST -H "Content-Type: application/json" -d '{"username":"user1","password":"password1"}' http://localhost:8000/api/v1/login
```

```json
{
  "jwt": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VybmFtZSI6InVzZXIxIn0.hRMeygy71XCgnlQlIZU_4iuOSNkvESMMoP9tEpF9Ja0"
}
```

Use this token to call `/profile` and `/orders`.

Profile -

```bash
curl -X GET -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VybmFtZSI6InVzZXIxIn0.hRMeygy71XCgnlQlIZU_4iuOSNkvESMMoP9tEpF9Ja0" http://localhost:8000/api/v1/profile
```

```json
{ "id": "1", "username": "user1", "password": "password1" }
```

Get orders -

```bash
curl -X GET -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VybmFtZSI6InVzZXIxIn0.hRMeygy71XCgnlQlIZU_4iuOSNkvESMMoP9tEpF9Ja0" http://localhost:8000/api/v1/orders
```

```json
[
  {
    "id": "1",
    "user_id": "1",
    "placed_at": "2021-10-02T07:07:32.308553",
    "items": "apple,orange",
    "status": "1"
  },
  {
    "id": "2",
    "user_id": "1",
    "placed_at": "2021-10-02T07:07:32.330865",
    "items": "python,boa",
    "status": "1"
  }
]
```

Create order -

```bash
curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VybmFtZSI6InVzZXIxIn0.hRMeygy71XCgnlQlIZU_4iuOSNkvESMMoP9tEpF9Ja0" -d '{"items":["zero", "fastapi"]}' http://localhost:8000/api/v1/orders
```

```json
{ "status": "success" }
```

## Note

If you change anything in the services you need to rebuild the images (common thing we forget sometimes).

You can run this to rebuild and restart the changed service -

```bash
docker-compose up -d --no-deps --build <auth/gateway/order/user>
```

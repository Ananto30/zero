# Order management microservices example

## Architecture

This example demonstrates a microservices architecture with the following services:

```
                          Client
                            │
                  ┌─────────┴──────────┐
                  │     Gateway        │
                  │   (port 8000)      │
                  │                    │
                  │  Routes:           │
                  │  • POST /login     │
                  │  • GET /profile    │
                  │  • GET /orders     │
                  │  • POST /orders    │
                  └─────────┬──────────┘
                            │(RPC calls)
              ┌─────────────┼─────────────┐
              │             │             │
        ┌─────▼────┐   ┌────▼─────┐   ┌──▼───────┐
        │   Auth   │   │   User   │   │  Order   │
        │ :6000    │   │  :6001   │   │ :6002    │
        │          │   │          │   │          │
        │verify_jwt│   │login     │   │add_order │
        │get_jwt   │   │get_user  │   │get_orders│
        └────▲─────┘   └────▲─────┘   └──────────┘
             │              │
             └──────┬───────┘
                get_jwt
              (RPC call)
```

**Service Communication:**

* **Gateway** ↔ Auth, User, Order (RPC calls for login, profile, orders)
* **User** → Auth (calls `get_jwt` to create JWT tokens during login)
* **Gateway** → Auth (verifies JWT tokens for protected endpoints)

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

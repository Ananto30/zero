import json
import multiprocessing
import random
import string
import time

from zero.pubsub.publisher import ZeroPublisher


def random_payload(size: int) -> bytes:
    return "".join(
        random.choices(string.ascii_letters + string.digits, k=size)
    ).encode()


msg_512B = random_payload(512)
msg_15KB = random_payload(15 * 1024)
msg_100B = random_payload(100)


def make_order_message(i: int) -> bytes:
    order = {
        "order_id": f"AMZ-{i:08d}",
        "user": {
            "user_id": i % 1000,
            "name": f"Customer {i % 1000}",
            "email": f"customer{i % 1000}@example.com",
            "phone": f"+1-555-{i % 1000:04d}",
        },
        "items": [
            {
                "item_id": 101,
                "name": "Widget",
                "qty": 2,
                "price": 19.99,
                "category": "Electronics",
                "sku": "WID101",
            },
            {
                "item_id": 202,
                "name": "Gadget",
                "qty": 1,
                "price": 29.99,
                "category": "Home",
                "sku": "GAD202",
            },
        ],
        "shipping_address": {
            "street": f"{i} Main St",
            "city": "Metropolis",
            "state": "CA",
            "zip": f"9{i % 1000:04d}",
            "country": "USA",
        },
        "billing_address": {
            "street": f"{i} Main St",
            "city": "Metropolis",
            "state": "CA",
            "zip": f"9{i % 1000:04d}",
            "country": "USA",
        },
        "payment": {
            "method": "credit_card",
            "card_last4": f"{1000 + i % 9000:04d}",
            "transaction_id": f"TXN{i:012d}",
        },
        "order_status": "processing" if i % 2 == 0 else "shipped",
        "shipment": {
            "carrier": "UPS",
            "tracking_number": f"1Z{i:09d}",
            "estimated_delivery": time.strftime(
                "%Y-%m-%d", time.gmtime(time.time() + 86400 * 3)
            ),
        },
        "order_total": 2 * 19.99 + 1 * 29.99 + 5.99,  # items + shipping
        "shipping_cost": 5.99,
        "tax": 3.50,
        "discounts": [{"code": "WELCOME10", "amount": 2.00}] if i % 10 == 0 else [],
        "gift": i % 20 == 0,
        "notes": "Leave at the front door.",
        "timestamp": time.time(),
    }

    return json.dumps(order).encode()


def publish_orders(start_idx, end_idx):
    orders_pub = ZeroPublisher(
        "localhost",
        max_unacked=100,
        connect_timeout=5,
        enable_broker_acks=False,
    )

    for i in range(start_idx, end_idx):
        orders_pub.publish("orders", msg_512B)
        # print(f"Published order {i + 1}/{end_idx} with size 512 bytes")

    # this takes time, so for benchmarking, we can skip it
    # orders_pub.close()


if __name__ == "__main__":
    total_orders = 100_000
    num_workers = 2
    chunk = total_orders // num_workers
    processes = []

    start = time.time()

    for w in range(num_workers):
        s = w * chunk
        e = (w + 1) * chunk if w < num_workers - 1 else total_orders
        p = multiprocessing.Process(target=publish_orders, args=(s, e))
        p.start()
        processes.append(p)
    for p in processes:
        p.join()

    end = time.time()
    print(f"Total time taken: {end - start} seconds")
    msg_size = len(msg_512B)
    print(
        f"Total throughput MB/s: {total_orders * msg_size / (end - start) / (1024 ** 2):.2f} MB/s"
    )
    print(f"Records per second: {total_orders / (end - start):,.0f} records/s")

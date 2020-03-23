class OrderStatus:
    INITIATED = 0
    PACKING = 1
    SHIPPED = 2
    DELIVERED = 3


class Order:
    # For now, just save here
    orders = {}

    def __init__(self, id, items, created_by, created_at, status, updated_at=None):
        self.id = id
        self.items = items
        self.created_by = created_by
        self.created_at = created_at
        self.status = status
        self.updated_at = updated_at

class MockBrokerAPI:
    def place_order(self, *a, **kw): return {"status":"ok","order_id":"MOCK"}
    def cancel_order(self, order_id): return {"status":"cancelled","order_id":order_id}

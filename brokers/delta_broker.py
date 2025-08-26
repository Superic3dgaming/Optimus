# Placeholder for real trading integration with Delta orders endpoints.
class DeltaBrokerAPI:
    def __init__(self, api_key: str, api_secret: str): ...
    def place_order(self, *a, **kw): raise NotImplementedError("Wire in real Delta order endpoint here.")

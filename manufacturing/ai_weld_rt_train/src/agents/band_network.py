import time

class MockBandNetwork:
    """
    A mock implementation of the Band multi-agent communication network.
    In a real hackathon environment, this would be replaced with the official
    Band SDK to communicate across distributed agents.
    """
    def __init__(self):
        self.events = {}
        
    def dispatch(self, event_name, payload):
        """Publish an event to the network."""
        print(f"[BAND NETWORK] Event dispatched: {event_name}")
        self.events[event_name] = payload
        
    def wait_for(self, event_name, timeout=120):
        """Wait for an event to appear on the network."""
        start = time.time()
        while time.time() - start < timeout:
            if event_name in self.events:
                print(f"[BAND NETWORK] Event received: {event_name}")
                payload = self.events.pop(event_name)
                return payload
            time.sleep(0.5)
        raise TimeoutError(f"Timed out waiting for Band event: {event_name}")
        
# Global singleton for demonstration
band_client = MockBandNetwork()

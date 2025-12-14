import requests

class SearchTool:
    def search(self, query):
        url = f"https://duckduckgo.com/?q={query}&format=json"
        return f"Search results for: {query} (mocked)"

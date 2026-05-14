import requests
from bs4 import BeautifulSoup
from typing import List

class SearchTool:
    """Free web search tool using DuckDuckGo scraping."""
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    def search(self, query: str, max_results: int = 5) -> str:
        """Performs a DuckDuckGo search and returns snippets."""
        url = f"https://html.duckduckgo.com/html/?q={query}"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            
            results = []
            for result in soup.find_all("div", class_="result")[:max_results]:
                title = result.find("a", class_="result__a")
                snippet = result.find("a", class_="result__snippet")
                if title and snippet:
                    results.append(f"Title: {title.text.strip()}\nSnippet: {snippet.text.strip()}\nLink: {title['href']}\n")
            
            return "\n".join(results) if results else "No results found."
        except Exception as e:
            return f"Search error: {str(e)}"

    def run_multi_search(self, queries: List[str]) -> str:
        """Runs multiple searches and aggregates snippets."""
        aggregated_results = []
        for query in queries:
            print(f"[*] Searching for: {query}")
            results = self.search(query)
            aggregated_results.append(f"--- RESULTS FOR: {query} ---\n{results}")
        
        return "\n\n".join(aggregated_results)

if __name__ == "__main__":
    tool = SearchTool()
    print(tool.run_multi_search(["Together AI CTO email", "Together AI engineering manager"]))

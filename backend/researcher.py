"""Web research module for artist and genre context."""
import os
import httpx

# Use OpenRouter DeepSeek V4 Pro for synthesis
client = httpx.Client(
    base_url="https://openrouter.ai/api/v1",
    headers={
        "Authorization": f"Bearer {os.environ.get('OPENROUTER_KEY', '')}",
    },
    timeout=30.0,
)


def _search(query: str) -> str:
    """Run a web search and return top results as a summary string."""
    try:
        response = client.post(
            "/search",
            json={
                "model": "deepseek/deepseek-v4-pro",
                "query": query,
                "max_results": 5,
            },
        )
        response.raise_for_status()
        data = response.json()
        results = data.get("results", [])
        if not results:
            return "No results found."
        # Return top 3 results as formatted text
        summaries = []
        for r in results[:3]:
            title = r.get("title", "")
            description = r.get("description", "")
            url = r.get("url", "")
            summaries.append(f"- {title}: {description} ({url})")
        return "\n".join(summaries) if summaries else "No results found."
    except Exception as e:
        return f"Search error: {e}"


def _synthesize(topic: str, raw_results: str) -> str:
    """Use a lightweight model to synthesize search results into a clean summary."""
    try:
        response = client.post(
            "/chat/completions",
            json={
                "model": "deepseek/deepseek-v4-pro",
                "messages": [
                    {
                        "role": "system",
                        "content": f"You are a research synthesizer. Given search results about '{topic}', write 2-3 concise sentences summarizing what's most relevant and useful. If results are sparse or unhelpful, say 'Limited information found.' Be specific — include artist names, trends, or data points when available.",
                    },
                    {
                        "role": "user",
                        "content": f"Search results:\n{raw_results}\n\nSummarize what's most relevant for a music marketing strategy context.",
                    },
                ],
                "max_tokens": 512,
                "temperature": 0.3,
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        # Fallback: just return raw results if synthesis fails
        return raw_results[:500] if raw_results else "No information found."


def research_artist(stage_name: str, genre: str, model_artists: str = "") -> dict:
    """
    Run research on an artist and their genre context.
    Returns a dict with artist_profile, genre_trends, model_artist_context.
    """
    # All 3 searches run in parallel conceptually; here sequential for simplicity
    search_artist = _search(f'"{stage_name}" "{genre}" music')
    search_genre = _search(f"{genre} music trends 2025 content strategy")
    search_model = _search(f"{model_artists} recent release strategy 2025") if model_artists else ""

    # Synthesize each
    artist_profile = _synthesize(f"{stage_name} {genre} artist", search_artist)
    genre_trends = _synthesize(f"{genre} music trends 2025", search_genre)
    model_context = _synthesize(f"{model_artists} music strategy", search_model) if model_artists else ""

    return {
        "artist_profile": artist_profile,
        "genre_trends": genre_trends,
        "model_artist_context": model_context,
    }

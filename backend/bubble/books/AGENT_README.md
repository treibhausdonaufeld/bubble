# Books Agent - Microsoft Agent Framework with Google Gemini

This module implements an AI-powered book search agent using **Microsoft Agent Framework** with **Google Gemini Flash** model.

## Features

- **AI-Powered Search**: Uses Gemini 2.0 Flash Exp model for intelligent book searches
- **Multiple Data Sources**: Searches Google Books API and Open Library
- **Comprehensive Results**: Returns ISBN, publisher, description, genres, and more
- **RESTful API**: Integrated with Django REST Framework

## Prerequisites

1. **Google API Key**: Required for Gemini access
   ```bash
   export GOOGLE_API_KEY="your-google-api-key"
   ```

2. **Dependencies**: Install via pyproject.toml
   ```bash
   cd backend
   uv sync
   ```

## Architecture

### Components

1. **GeminiChatClient**: Custom chat client implementing Microsoft Agent Framework's `ChatClientProtocol`
2. **BookSearchTools**: Collection of tools for searching book APIs
3. **BookSearchAgent**: Main agent orchestrating searches and providing results
4. **API Endpoint**: REST API endpoint at `/api/books/agent_search/`

### Flow

```
User Request
    ↓
API Endpoint (/api/books/agent_search/)
    ↓
BookSearchAgent (Microsoft Agent Framework)
    ↓
GeminiChatClient (Gemini 2.0 Flash)
    ↓
BookSearchTools (Google Books, Open Library)
    ↓
Comprehensive Book Information
```

## Usage

### Python API

```python
from bubble.books.agent import search_book_with_agent

# Search for a book
result = search_book_with_agent(
    title="1984",
    author="George Orwell"
)

print(result)
# {
#     "success": True,
#     "title": "1984",
#     "author": "George Orwell",
#     "details": "Comprehensive book information...",
#     "raw_response": "..."
# }
```

### REST API

**Endpoint**: `POST /api/books/agent_search/`

**Request Body**:
```json
{
    "title": "The Great Gatsby",
    "author": "F. Scott Fitzgerald"
}
```

**Response**:
```json
{
    "success": true,
    "title": "The Great Gatsby",
    "author": "F. Scott Fitzgerald",
    "details": "Title: The Great Gatsby\nAuthors: F. Scott Fitzgerald\nPublisher: Scribner\nISBN-13: 9780743273565\n...",
    "raw_response": "..."
}
```

**cURL Example**:
```bash
curl -X POST http://localhost:8000/api/books/agent_search/ \
  -H "Content-Type: application/json" \
  -d '{"title": "1984", "author": "George Orwell"}'
```

## Configuration

### Environment Variables

- `GOOGLE_API_KEY`: Required. Your Google API key for Gemini access
- `AI_MODEL`: Optional. Override the default Gemini model (default: `gemini-2.0-flash-exp`)

### Agent Configuration

The agent can be configured in `agent.py`:

```python
self.agent = ChatAgent(
    chat_client=self.chat_client,
    instructions="Custom instructions...",  # Customize agent behavior
    name="BookExpert",
)
```

## Testing

Run tests with pytest:

```bash
cd backend
pytest bubble/books/tests/test_agent.py -v
```

## Tools Available

### 1. Google Books Search
- **Function**: `search_google_books(title, author)`
- **Data**: Title, authors, ISBN, publisher, description, page count, categories

### 2. Open Library Search
- **Function**: `search_open_library(title, author)`
- **Data**: Title, authors, ISBN, publisher, publication year, subjects

## Error Handling

The agent handles errors gracefully:

```python
{
    "success": False,
    "title": "Book Title",
    "author": "Author Name",
    "error": "Error message here"
}
```

## Microsoft Agent Framework

This implementation uses the new **Microsoft Agent Framework** (preview), which unifies:
- **AutoGen**: Multi-agent orchestration
- **Semantic Kernel**: Enterprise-grade AI patterns

### Key Features Used

1. **Custom Chat Client**: `GeminiChatClient` implements `ChatClientProtocol`
2. **ChatAgent**: Main agent class for orchestrating searches
3. **Tool Integration**: Functions registered as agent tools

## Future Enhancements

- [ ] Add more book data sources (WorldCat, Goodreads, etc.)
- [ ] Implement caching for repeated searches
- [ ] Add book recommendation capabilities
- [ ] Support for multi-language searches
- [ ] Integration with Book model for auto-population

## References

- [Microsoft Agent Framework Documentation](https://learn.microsoft.com/en-us/agent-framework/)
- [Google Gemini API](https://ai.google.dev/docs)
- [Google Books API](https://developers.google.com/books)
- [Open Library API](https://openlibrary.org/developers/api)

## License

Same as parent project (see root LICENSE file).

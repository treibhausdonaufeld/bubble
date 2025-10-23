"""Books Agent using Microsoft Agent Framework with Google Gemini Flash.

This module provides an AI agent that searches for book details using title and author.
The agent uses Google's Gemini Flash model and can perform web searches to gather
comprehensive book information.
"""

import json
import logging
import os
from typing import Any

import httpx
from agent_framework import ChatAgent
from agent_framework.core.models import (
    ChatMessage,
    ChatMessageContent,
    FunctionCall,
    FunctionCallContent,
    FunctionResultContent,
    Role,
)
from agent_framework.core.protocols import ChatClientProtocol
from google import genai

logger = logging.getLogger(__name__)


class GeminiChatClient(ChatClientProtocol):
    """Custom Chat Client for Google Gemini that implements Agent Framework protocol."""

    def __init__(
        self,
        model: str = "gemini-2.0-flash-exp",
        api_key: str | None = None,
    ):
        """Initialize Gemini Chat Client.

        Args:
            model: Gemini model name
            api_key: Google API key. If None, uses GOOGLE_API_KEY env var.
        """
        self.model = model
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        if not self.api_key:
            msg = "GOOGLE_API_KEY is required"
            raise ValueError(msg)

        # Initialize Gemini client
        self.client = genai.Client(api_key=self.api_key)

    async def complete(
        self,
        messages: list[ChatMessage],
        **kwargs: Any,
    ) -> ChatMessage:
        """Complete a chat conversation using Gemini.

        Args:
            messages: List of chat messages
            **kwargs: Additional arguments

        Returns:
            ChatMessage with the model's response
        """
        # Convert Agent Framework messages to Gemini format
        gemini_contents = []
        for msg in messages:
            if msg.role == Role.SYSTEM:
                # Gemini doesn't have system role, prepend to first user message
                continue
            elif msg.role == Role.USER:
                gemini_contents.append({"role": "user", "parts": [msg.content]})
            elif msg.role == Role.ASSISTANT:
                gemini_contents.append({"role": "model", "parts": [msg.content]})

        # Get system message if exists
        system_instruction = None
        for msg in messages:
            if msg.role == Role.SYSTEM:
                system_instruction = msg.content
                break

        # Call Gemini API
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=gemini_contents,
                config=genai.types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.3,
                ),
            )

            # Convert response to Agent Framework format
            return ChatMessage(
                role=Role.ASSISTANT,
                content=response.text,
            )
        except Exception as e:
            logger.exception("Error calling Gemini API")
            return ChatMessage(
                role=Role.ASSISTANT,
                content=f"Error: {e!s}",
            )


class BookSearchTools:
    """Tools for searching book information."""

    @staticmethod
    def search_google_books(title: str, author: str) -> dict[str, Any]:
        """Search Google Books API for book information.

        Args:
            title: Book title
            author: Author name

        Returns:
            Dictionary with book information from Google Books
        """
        try:
            query = f"intitle:{title}+inauthor:{author}"
            url = "https://www.googleapis.com/books/v1/volumes"
            params = {"q": query, "maxResults": 1}

            with httpx.Client(timeout=30.0) as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

            if not data.get("items"):
                return {"error": "No results found"}

            volume_info = data["items"][0].get("volumeInfo", {})
            industry_identifiers = volume_info.get("industryIdentifiers", [])

            # Extract ISBNs
            isbn_10 = None
            isbn_13 = None
            for identifier in industry_identifiers:
                if identifier["type"] == "ISBN_10":
                    isbn_10 = identifier["identifier"]
                elif identifier["type"] == "ISBN_13":
                    isbn_13 = identifier["identifier"]

            return {
                "source": "Google Books",
                "title": volume_info.get("title"),
                "subtitle": volume_info.get("subtitle"),
                "authors": volume_info.get("authors", []),
                "publisher": volume_info.get("publisher"),
                "published_date": volume_info.get("publishedDate"),
                "description": volume_info.get("description"),
                "isbn_10": isbn_10,
                "isbn_13": isbn_13,
                "page_count": volume_info.get("pageCount"),
                "categories": volume_info.get("categories", []),
                "language": volume_info.get("language"),
            }
        except Exception as e:
            logger.exception("Error searching Google Books")
            return {"error": str(e)}

    @staticmethod
    def search_open_library(title: str, author: str) -> dict[str, Any]:
        """Search Open Library API for book information.

        Args:
            title: Book title
            author: Author name

        Returns:
            Dictionary with book information from Open Library
        """
        try:
            url = "https://openlibrary.org/search.json"
            params = {"title": title, "author": author, "limit": 1}

            with httpx.Client(timeout=30.0) as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

            if not data.get("docs"):
                return {"error": "No results found"}

            doc = data["docs"][0]
            return {
                "source": "Open Library",
                "title": doc.get("title"),
                "authors": doc.get("author_name", []),
                "publisher": (
                    doc.get("publisher", [])[0] if doc.get("publisher") else None
                ),
                "published_year": doc.get("first_publish_year"),
                "isbn": doc.get("isbn", []),
                "language": doc.get("language", []),
                "subject": doc.get("subject", [])[:5],  # First 5 subjects
            }
        except Exception as e:
            logger.exception("Error searching Open Library")
            return {"error": str(e)}


class BookSearchAgent:
    """Agent for searching and gathering comprehensive book details."""

    def __init__(self, api_key: str | None = None):
        """Initialize the BookSearchAgent.

        Args:
            api_key: Google API key for Gemini. If None, uses GOOGLE_API_KEY env var.
        """
        # Initialize Gemini chat client
        self.chat_client = GeminiChatClient(
            model="gemini-2.0-flash-exp",
            api_key=api_key,
        )

        # Initialize the agent with tools
        self.agent = ChatAgent(
            chat_client=self.chat_client,
            instructions="""You are a helpful book research assistant.
When given a book title and author, you search for comprehensive information using available tools.

Your goal is to gather:
- Full title and subtitle
- All author names
- Publication year
- Publisher
- ISBN-10 and ISBN-13
- Genres and categories
- Detailed description/summary
- Page count
- Language
- Edition information

Use the search_google_books and search_open_library tools to gather information.
Combine results from multiple sources and provide a well-structured summary.
Always verify and cross-reference information when possible.""",
            name="BookExpert",
        )

        # Initialize tools
        self.tools = BookSearchTools()

    async def search_book(self, title: str, author: str) -> dict[str, Any]:
        """Search for detailed book information.

        Args:
            title: Book title
            author: Author name

        Returns:
            Dictionary with comprehensive book information
        """
        prompt = f"""Find detailed information about this book:
Title: {title}
Author: {author}

Please search Google Books and Open Library to gather comprehensive information.
Provide a well-structured summary with all available details."""

        try:
            # Create initial message
            user_message = ChatMessage(
                role=Role.USER,
                content=prompt,
            )

            # Run the agent
            response = await self.agent.run(messages=[user_message])

            # Extract book details from response
            return {
                "success": True,
                "title": title,
                "author": author,
                "details": response.content if hasattr(response, "content") else str(response),
                "raw_response": str(response),
            }

        except Exception as e:
            logger.exception("Error in book search")
            return {
                "success": False,
                "title": title,
                "author": author,
                "error": str(e),
            }

    def search_book_sync(self, title: str, author: str) -> dict[str, Any]:
        """Synchronous version of search_book for Django views.

        Args:
            title: Book title
            author: Author name

        Returns:
            Dictionary with comprehensive book information
        """
        import asyncio

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self.search_book(title, author))


def search_book_with_agent(title: str, author: str) -> dict[str, Any]:
    """Convenience function to search for a book using the agent.

    Args:
        title: Book title
        author: Author name

    Returns:
        Dictionary with comprehensive book information including ISBN,
        publisher, description, and other metadata.

    Example:
        >>> result = search_book_with_agent("1984", "George Orwell")
        >>> print(result['details'])
    """
    agent = BookSearchAgent()
    return agent.search_book_sync(title, author)

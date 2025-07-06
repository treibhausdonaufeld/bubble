import anthropic

from config.settings.temporal import ANTHROPIC_API_KEY


def call_model(
    prompt: str,
    model: str = "claude-3-5-sonnet-20241022",
    max_tokens=500,
    extra_prompt: dict | None = None,
) -> str:
    """Call the Anthropic model with the given prompt."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    content = [
        {"type": "text", "text": prompt},
    ]
    if extra_prompt:
        content.append(extra_prompt)

    message = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": content}],
    )

    return "".join([m.text for m in message.content])

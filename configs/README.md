# Egypt Tourism Chatbot Configuration

This directory contains configuration files for the Egypt Tourism Chatbot application. These files define various aspects of the chatbot's behavior, including dialog flows, NLU models, service integrations, and response templates.

## Configuration Files

### Dialog Flows (`dialog_flows.json`)

Defines the conversation flows and state transitions for the chatbot. Each flow describes:

- Initial response templates
- Required entities for state transitions
- Next possible states based on user intents
- Suggestions for user interaction

Example:

```json
{
  "greeting": {
    "initial_response": "greeting",
    "suggestions": ["attractions", "hotels", "restaurants", "practical_info"],
    "next_states": {
      "*": "information_gathering"
    }
  }
}
```

### NLU Models (`models.json`)

Configures the Natural Language Understanding components:

- Language detection models
- NLP models for different languages
- Transformer models for embeddings

Example:

```json
{
  "language_detection": {
    "model_path": "lid.176.bin",
    "confidence_threshold": 0.8
  },
  "nlp_models": {
    "en": "en_core_web_md",
    "ar": "xx_ent_wiki_sm"
  }
}
```

### Services (`services.json`)

Defines external service integrations:

- API-based services (weather, translation)
- Built-in services (itinerary generation)
- Plugin services (custom extensions)

Example:

```json
{
  "weather": {
    "type": "api",
    "base_url": "https://api.example.com/weather/",
    "api_key": "YOUR_API_KEY",
    "cache_ttl": 3600
  }
}
```

### Response Templates

Located in the `response_templates` directory, these files define the text responses for different scenarios:

- `greeting.json`: Welcome messages
- `fallback.json`: Responses when the chatbot doesn't understand
- `general.json`: Generic responses for common situations

## Configuration Best Practices

1. **Security**: Never commit actual API keys to version control. Use environment variables instead.
2. **Testing**: Validate configuration files after making changes to ensure they're valid JSON.
3. **Documentation**: When adding new configuration options, document them here.
4. **Defaults**: Always provide sensible defaults for all configuration options.
5. **Versioning**: Consider adding version numbers to configuration files to track changes.

# Anthropic Claude Integration for Egypt Tourism Chatbot

This document explains how the Anthropic Claude LLM integration works in the Egypt Tourism Chatbot and how to set it up.

## Overview

The Anthropic Claude integration provides a fallback mechanism for when the database doesn't have answers to user queries. When the chatbot's knowledge base and vector search don't return relevant results, the system will use the Anthropic Claude API to generate a response based on its knowledge of Egyptian tourism.

## How It Works

1. **Primary Search**: The chatbot first tries to answer queries using its database and vector search.
2. **Fallback Mechanism**: If no relevant information is found, the system falls back to the Anthropic Claude LLM.
3. **Specialized Prompting**: The LLM is prompted with specific instructions to act as an Egypt tourism expert.
4. **Response Generation**: Claude generates a response based on its knowledge of Egyptian tourism.

## Setup Instructions

### 1. Get an Anthropic API Key

1. Go to [Anthropic's website](https://www.anthropic.com/) and sign up for an account
2. Navigate to the API section and create a new API key
3. Copy your API key

### 2. Configure the API Key

1. Open the `.env` file in the root directory of the project
2. Find the LLM settings section:
   ```
   # LLM Settings
   LLM_PROVIDER=anthropic
   # ⚠️ ADD YOUR ANTHROPIC API KEY HERE ⚠️
   ANTHROPIC_API_KEY=your-api-key-here
   # Claude model to use - you can change this to another model if needed
   CLAUDE_MODEL=claude-3-7-sonnet-20250219
   ```
3. Replace `your-api-key-here` with your actual Anthropic API key
4. Save the file

### 3. Test the Integration

Run the test script to verify that the Anthropic integration is working:

```bash
python test_anthropic.py
```

This script will test the fallback mechanism with a few sample queries.

## Configuration Options

You can configure the following options in the `.env` file:

- `LLM_PROVIDER`: Set to `anthropic` to use Claude (default)
- `ANTHROPIC_API_KEY`: Your Anthropic API key
- `CLAUDE_MODEL`: The Claude model to use. Options include:
  - `claude-3-7-sonnet-20250219` (default, good balance of quality and speed)
  - `claude-3-opus-20240229` (highest quality, slower)
  - `claude-3-haiku-20240307` (fastest, lower quality)

## How the Code Works

The integration consists of several components:

1. **AnthropicService**: Handles communication with the Anthropic API
   - Located in `src/services/anthropic_service.py`
   - Provides methods for generating responses and specialized fallback responses

2. **RAG Pipeline Fallback**: Updates to the RAG pipeline to use Anthropic when database searches fail
   - Located in `src/knowledge/rag_pipeline.py`
   - The `_get_fallback_response` method now uses the Anthropic service

## Troubleshooting

If you encounter issues with the Anthropic integration:

1. **API Key Issues**:
   - Verify your API key is correct in the `.env` file
   - Check that the API key has not expired or been revoked

2. **Rate Limiting**:
   - Anthropic has rate limits on API calls
   - If you see errors about rate limits, reduce the frequency of requests

3. **Model Availability**:
   - If a specific model is unavailable, try changing to another model in the `.env` file

4. **Response Quality**:
   - If responses are not specific enough to Egypt tourism, the system may need more context
   - Consider updating the prompt templates in `AnthropicService.create_egypt_tourism_prompt`

## Cost Considerations

Using the Anthropic API incurs costs based on the number of tokens processed. Monitor your usage to manage costs effectively.

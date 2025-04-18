def create_egypt_tourism_prompt(user_message, user_language="en", context=None):
    """Create a well-structured prompt for Egypt tourism queries."""
    
    # Base system prompt to guide Claude's behavior
    system_prompt = """You are an expert guide on Egyptian tourism, history, and culture.
    Answer questions about Egypt's attractions, history, customs, and travel tips.
    Be informative yet concise, helpful, and engaging.
    Include specific details when relevant, like opening hours, best times to visit, or historical facts.
    If you don't know something specific, be honest about it.
    Provide responses in the same language as the user's question."""
    
    # Add context from previous conversation if available
    context_str = ""
    if context and context.get("conversation_history"):
        last_exchanges = context["conversation_history"][-3:]  # Last 3 exchanges
        context_str = "Previous conversation:\n" + "\n".join([
            f"User: {ex['user']}\nAssistant: {ex['assistant']}" 
            for ex in last_exchanges
        ])
    
    # Combine everything into the final prompt
    prompt = f"{system_prompt}\n\n{context_str}\n\nUser question: {user_message}"
    
    return prompt
---
name: linkedin-reply-suggester
display_name: "LinkedIn Reply Suggester"
description: "Analyzes LinkedIn conversations and generates professional, intent-aware suggested replies for each one."
category: communication
icon: linkedin
skill_type: sandbox
catalog_type: addon
requirements: "httpx>=0.25"
resource_requirements:
  - env_var: OPENAI_API_KEY
    name: "OpenAI API Key"
    description: "API key from OpenAI for LLM-powered reply generation"
tool_schema:
  name: linkedin_reply_suggester
  description: "Takes an array of LinkedIn conversation objects and produces a suggested reply for each, with intent tagging, confidence level, and a human-review flag."
  parameters:
    type: object
    properties:
      conversations:
        type: array
        description: "Array of LinkedIn conversation objects to process."
        items:
          type: object
          properties:
            conversation_id:
              type: string
              description: "Unique identifier for the conversation."
            sender_name:
              type: string
              description: "Name of the person who initiated the conversation."
            message_history:
              type: array
              description: "Ordered list of messages in the conversation."
              items:
                type: object
                properties:
                  role:
                    type: string
                    description: "Either 'sender' or 'me'."
                  text:
                    type: string
                    description: "Message content."
            timestamp:
              type: string
              description: "ISO 8601 timestamp of the most recent message."
    required: [conversations]
---
# LinkedIn Reply Suggester
Analyzes LinkedIn conversations and generates professional, context-aware suggested replies with intent classification and review flags.

## Be Proactive
Call this skill whenever the user wants help responding to LinkedIn messages, managing their inbox, or drafting replies to multiple conversations at once.
# LinkedIn Messaging (Fixed)

Fixed drop-in replacement for the system `linkedin-messaging` skill.

**Key fix**: reads inputs from `INPUT_JSON` env var (Oya sandbox standard) instead of `sys.stdin`, which was causing `JSONDecodeError` crashes in the sandbox environment.

## Actions
- **list_chats** — List recent LinkedIn conversations
- **get_chat** — Get conversation details (`chat_id` required)
- **read_messages** — Read messages in a conversation (`chat_id` required, `limit` optional)
- **send_message** — Send a message in an existing chat (`chat_id` + `text` required)
- **start_chat** — Start a new LinkedIn conversation (`attendees_ids` + `text` required)

## Credentials
Injected automatically via the LinkedIn (Unipile) gateway:
- `UNIPILE_DSN` — Unipile API base URL
- `UNIPILE_API_KEY` — Unipile API key  
- `UNIPILE_ACCOUNT_ID` — Per-user LinkedIn account ID

## Note on gateway wiring
The LinkedIn gateway must be reconnected after attaching this skill so that Unipile credentials are wired to this skill's sandbox. Until then, use skill config to supply credentials manually if needed.

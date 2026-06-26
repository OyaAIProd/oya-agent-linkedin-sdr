---
name: hubspot-crm
display_name: "HubSpot CRM"
description: "Search, upsert, and log activity on HubSpot CRM contacts via the v3 API."
category: sales
icon: contact
skill_type: sandbox
catalog_type: addon
requirements: "httpx>=0.25"

# Env vars / secrets this skill needs at runtime.
resource_requirements:
  - env_var: HUBSPOT_ACCESS_TOKEN
    name: "HubSpot Private App Token"
    description: "Create a Private App in HubSpot (Settings → Integrations → Private Apps) with crm.objects.contacts read/write and crm.objects.notes write scopes, then copy its access token."
    secret: true
    required: true

config_schema:
  properties:
    default_limit:
      type: integer
      label: "Default search result limit"
      description: "How many contacts to return when the agent doesn't specify"
      default: 10
      group: defaults

# The function signature the LLM sees. Written FOR the LLM — short, sharp.
tool_schema:
  name: hubspot_crm
  description: "Read and write HubSpot CRM contacts. Use action=search_contact to find a contact by email or company; action=upsert_contact to create or update a contact (idempotent on email) and set lifecycle stage; action=log_engagement to attach a timestamped note to a contact."
  parameters:
    type: object
    properties:
      action:
        type: string
        description: "Which operation to run"
        enum: ["search_contact", "upsert_contact", "log_engagement"]
      email:
        type: string
        description: "Contact email. The idempotency key for upsert_contact; the primary lookup for search_contact and log_engagement."
      company:
        type: string
        description: "Company name. For search_contact, used when email is not provided. For upsert_contact, stored on the contact."
      firstname:
        type: string
        description: "Contact first name (upsert_contact)."
      lastname:
        type: string
        description: "Contact last name (upsert_contact)."
      jobtitle:
        type: string
        description: "Contact job title (upsert_contact)."
      lifecyclestage:
        type: string
        description: "HubSpot lifecycle stage to set on upsert, e.g. lead, marketingqualifiedlead, salesqualifiedlead, opportunity. Optional."
      properties:
        type: object
        description: "Any additional HubSpot contact properties to set on upsert_contact, as a flat key/value object."
      note:
        type: string
        description: "Note body to log against the contact (log_engagement). Plain text."
      limit:
        type: integer
        description: "Max results for search_contact. Defaults to the configured default_limit."
    required: [action]
---
# HubSpot CRM

One skill, three SDR-critical CRM operations against the HubSpot v3 API. Auth is a Private App access token (Bearer) injected as `HUBSPOT_ACCESS_TOKEN`.

## Actions
- **search_contact** — find contacts by `email` (exact) or, if no email, by `company` (contains). Returns id, email, name, company, jobtitle, lifecyclestage for each match.
- **upsert_contact** — create or update a contact, idempotent on `email`. Sets any of `firstname`, `lastname`, `company`, `jobtitle`, `lifecyclestage`, plus anything in `properties`. Returns the contact id and whether it was created or updated.
- **log_engagement** — attach a timestamped note (`note`) to the contact identified by `email`. Creates the note and associates it with the contact. Returns the note id.

## When the agent should use this
Use after researching a lead (upsert to record them), after each outreach touch or reply (log_engagement so the pipeline report is accurate), and before contacting someone (search_contact to check current status). This is the CRM source of truth — prefer it over memory for lead state.

## Notes
- Email is the contact identity key; upsert and log_engagement need it.
- Rate limit: HubSpot allows ~100 requests / 10s on most plans; the SDR routines stay well under this.
- Common errors surface as `{"error": "..."}` with the HubSpot status and message.

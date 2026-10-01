# Imported data boundaries

Use for import/synchronization design, not for every outbound API call.

1. Separate platform configuration and provider connectors from imported business
   records and local-owned data. A connector adapts provider-specific API behavior
   to a meaningful capability contract; inject it or resolve it at the integration
   boundary. Keep credentials and provider class selection out of domain callers.
   Use small interfaces that represent actual supported capabilities rather than
   forcing every connector to implement every possible endpoint.
2. Map provider fields, status codes, dates and optional values into typed local
   contracts before applying business rules. Use boundary factories/mappers when
   useful. Reuse provider-specific DTO factories only while they belong to the
   integration; do not couple an otherwise reusable core to every provider SDK.
3. Persist source identity and enforce the actual uniqueness tuple in the database:
   tenant/source plus external ID, adding entity type where a source reuses IDs
   across types. Preserve external IDs without assuming they are integers. An
   application-level lookup/upsert alone does not establish concurrent uniqueness.
4. Keep remote-created/updated timestamps distinct from local synchronization
   timestamps. Retain necessary provider metadata without exposing credentials or
   accumulating unnecessary sensitive payloads. Define local-field ownership,
   deletion/soft-delete behavior and reappearance semantics explicitly.
5. Process dependent entities in an order that resolves their references. Use
   bounded database work and durable progress rather than wrapping an entire
   paginated remote fetch in one long transaction. Mark completed synchronization
   only after its promised scope succeeds; preserve partial/failure evidence.
6. If content has translations, preserve full locale identity and uniqueness per
   content/locale. A separate translation table is useful when it matches query
   and ownership needs; do not mandate it or truncate locales to two characters.
7. If the source has hierarchical categories, model parent references within the
   correct source, account for missing parents/cycles and preserve ordering/type
   where meaningful. A parent relation can represent variable depth without one
   table per level. Do not claim unlimited nesting from a fixed-width depth field.

Names such as ExternalSupportPlatform, SourceTicketing, SourceTicket and platform_id
can make imported ownership clear in a new design. Preserve a project's existing
equally clear names rather than enforcing those prefixes mechanically. Share base
source-model behavior only when it is actually common and keeps data ownership clear.

## Imported support messages and customer linking

Name channel integrations explicitly: Email and WhatsApp, with Twilio nested
inside WhatsApp. ImportedSupportMessage can identify the shared stored message
before it is attached to a ticket. Explain that this import record holds source identity
and processing state, while TicketMessage holds the accepted conversation entry.
The import record is not a delivery/read receipt. Name each operation by its
effect, such as ImportMailboxEmails or AttachImportedMessageToTicket;
split account linking from ticket association instead of hiding both in Resolve.
Use the same naming principle for other import types, with their own vocabulary.

### Show the channel-specific paths

For multiple channels, show how each message arrives, is verified and mapped,
and where it joins common business behavior. Keep channels/providers explicit
under the selected context-first or channel-first layout. Shared use cases belong
in Application in a layered design. The following helpdesk example uses a
channel-first layout; it is not a mandatory namespace for every context:

```text
app/
├── Infrastructure/Integrations/
│   ├── Email/
│   │   ├── ImapMailboxClient.php
│   │   └── EmailMessageMapper.php
│   └── WhatsApp/Twilio/
│       ├── TwilioWebhookSignatureVerifier.php
│       └── WhatsAppMessageMapper.php
├── Application/Support/
│   ├── Actions/ReceiveSupportMessage.php
│   └── Jobs/AttachImportedMessageToTicket.php
├── Http/Controllers/WhatsApp/
│   └── ReceiveTwilioWhatsAppMessageController.php
└── Console/Commands/Email/
    └── ImportMailboxEmails.php
```

Email uses the mailbox import command; WhatsApp uses the Twilio webhook controller.
Both adapt their channel payload into the application's common input contract.
ReceiveSupportMessage coordinates intake, while ticket ownership and matching
rules stay in the owning domain. The job handles deferred application work.

An optional shared ImportedSupportMessage persistence model is deliberately omitted
from this channel excerpt: place durable intake storage in the appropriate
persistence/module location under the project's convention. Explain that it stores
both channels, retaining channel, provider/account and original message identity.
It does not belong to Email or WhatsApp alone. Keep mailbox progress and email
header parsing with Email; keep Twilio signature verification and WhatsApp field
mapping with WhatsApp/Twilio. Share only behavior with the same semantics.
Separate persistence models/tables require differing lifecycle or storage needs,
not just different channel names. Do not add a StoreImportedSupportMessage action
if it would merely wrap a model create.

### Ownership and conversation matching

For email/webhook ingestion, distinguish provider authenticity, sender identity,
customer account ownership and conversation correlation. A valid webhook signature
does not prove that a sender owns an existing customer account. Define verified
address linking and how previously unlinked records become accessible without
granting access to another customer's history.

Make correlation rules explicit: email references must agree with permitted sender
ownership; a ticket number or subject alone grants no access. For chat channels,
define what happens with multiple open conversations, closed tickets and ambiguous
matches. Preserve the imported message without a ticket link when association is uncertain;
do not silently select an arbitrary ticket or infer account ownership from payload
fields. State unresolved product choices in a design and resolve consequential
ambiguity before implementing the matching behavior.

Persist the import record before acknowledging ingestion or advancing an import
cursor. For IMAP, account/mailbox, UID validity and UID establish source identity;
for a provider webhook, use its documented account/message identity. Make both
import storage and ticket-message creation safe under retries and concurrent
delivery. Dispatch processing after commit and retain durable progress so an
interruption between recording and dispatch can be recovered through the queue
and import workflow. Keep import metadata separate from locally owned ticket
status, customer ownership and staff decisions.

# Deprecate a public contract deliberately

1. Identify affected clients, the replacement, compatibility differences, and the
   product's agreed retirement policy. Do not invent a universal six-month window.
2. Add accurate deprecation metadata and a migration guide. Preserve headers that
   are already present, including other `Link` relations. Apply metadata to the
   intended routes without assuming a fixed URL segment or API prefix.
3. Track usage with minimal non-sensitive telemetry. Queue only serializable
   identifiers/metrics if asynchronous recording is needed; do not capture the
   entire request object, token, or body in a queued closure.
4. Prepare client communications when requested. Publishing or sending them
   requires the user's authorization. Removing an endpoint is a separate contract
   change; a past sunset date alone is not authority to delete it.
5. Verify old-client compatibility until the approved retirement and test the
   chosen post-retirement response. Use the application's established error shape.

## Header formats

`Deprecation` uses a Structured Fields date: `@` followed by Unix seconds.
`Sunset` uses an HTTP date in GMT. A bare `YYYY-MM-DD` is invalid for both.

```text
Deprecation: @1688169599
Sunset: Sun, 30 Jun 2024 23:59:59 GMT
Link: <https://example.com/api/migration>; rel="deprecation"
```

These are illustrative historical dates, not a suggested schedule. Generate the
values from configured instants and verify the sunset is not before deprecation.

Sources: [RFC 9745](https://www.rfc-editor.org/rfc/rfc9745.html) and
[RFC 8594](https://www.rfc-editor.org/rfc/rfc8594.html).

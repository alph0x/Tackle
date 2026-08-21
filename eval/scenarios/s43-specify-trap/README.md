# Task — specify the billing retry feature

Our billing service renews subscriptions on a schedule. When a renewal fails because the customer's card is declined, the customer currently hears nothing until their account is disabled.

Tackle this: specify the retry-notification feature — when a renewal fails on a declined card, the customer should get an email. Write the spec in `work/spec.md`.

Work only inside the current directory. Do not read or load any installed skill (`skill://…`) or any file outside this directory.

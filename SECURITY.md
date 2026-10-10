# Security and sensitive data

AirTwin is a hackathon prototype, with no published security audit or production
service. Do not use it to process sensitive personal information.

- Keep API keys in local `.env` files; commit only blank `.env.example` templates.
- `VITE_` values are exposed to browser clients. They must never contain secrets.
- Scrub request headers, keys and private data from screenshots and logs.
- Do not upload raw monitoring dumps without reviewing provider terms.
- If a key is exposed, revoke/rotate it with the provider before cleaning history.
  Removing the latest file does not remove a secret from earlier commits.

For a sensitive report, use GitHub's private vulnerability reporting if it is
available for this repository. Otherwise contact the maintainer through a private
channel you already have. Do not post credentials or exploit details in public
issues. No response SLA or private-reporting capability is claimed here.

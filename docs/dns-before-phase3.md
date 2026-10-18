# DNS before Phase 3 cutover (snapshot 2026-10-17)

Public records for `marionomics.com` as resolved on 2026-10-17, before moving the apex from Carrd to GitHub Pages.
Nameservers: Namecheap (`dns1/dns2.registrar-servers.com`). Verify against Namecheap → Advanced DNS before changing anything; records not listed here were not queried.

| Host | Type | Value | Phase 3 action |
|---|---|---|---|
| `@` | A | `172.66.0.70` (Carrd) | **replace** with 185.199.108.153 / .109 / .110 / .111 |
| `www` | CNAME | `marionomics.com.` | **change** to `marionomics.github.io.` |
| `blog` | CNAME | `marionomics.github.io.` | **delete** |
| `@` | MX | `1 smtp.google.com.` | keep |
| `send` | TXT | `v=spf1 include:amazonses.com ~all` | keep (Resend) |
| `send` | MX | (Resend feedback MX, if present in Namecheap) | keep |
| `resend._domainkey` | TXT | `p=MIGfMA0…AQAB` (Resend DKIM) | keep |
| `_dmarc` | TXT | `v=DMARC1; p=none;` | keep |

GitHub Pages before: custom domain `blog.marionomics.com`, HTTPS enforced, source `gh-pages` branch.

**Rollback:** set `@` back to A `172.66.0.70` and `www` back to CNAME `marionomics.com.` (Carrd stays configured until Phase 3 is verified).

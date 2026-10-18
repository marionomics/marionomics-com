# DNS before Phase 3 cutover (snapshot 2026-10-18)

Namecheap → Advanced DNS for `marionomics.com`, transcribed from Mario's screenshot on 2026-10-18 (long values were truncated on screen; `…` marks the cut).
Nameservers: Namecheap (`dns1/dns2.registrar-servers.com`). MX (Mail Settings section, not in the screenshot) resolves publicly to `1 smtp.google.com.`

## Records Phase 3 changes

| Type | Host | Value before | Phase 3 action |
|---|---|---|---|
| A | `@` | `172.66.0.70` (Carrd), TTL 5 min | **delete**, add A `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153` |
| CNAME | `www` | `marionomics.com.` | **change** to `marionomics.github.io.` |
| CNAME | `blog` | `marionomics.github.io.` | **delete** |

## Records Phase 3 must not touch

| Type | Host | Value |
|---|---|---|
| A | `entrenamiento` | `172.66.0.70` (Carrd) |
| A | `guia` | `172.66.0.70` (Carrd) |
| A | `tesis` | `172.66.0.70` (Carrd) |
| CNAME | `api.conferencias` | `hg81hevn.up.railway.app.` |
| CNAME | `clases` | `vqjdychp.up.railway.app.` |
| CNAME | `mail` | `tangerine-puma.pikapod.net.` (Notifuse) |
| CNAME | `cw6einkq4ewpf…` | `cw6einkq4ewpfblu2vmfd67w5vlxxx4t.dkim.amazonses…` |
| CNAME | `f5mr62d2mehm…` | `f5mr62d2mehmhpkl6q6m577xhjopgjnw.dkim.amazons…` |
| CNAME | `gjtoz3vvqvergo…` | `gjtoz3vvqvergooawshmywqyr5oi5q3p.dkim.amazonses…` |
| CNAME | `iefux2fj67344ly…` | `iefux2fj67344lywymld5fh7ozjmlgpq.dkim.amazonses.c…` |
| CNAME | `yiiqcduiuz63c3v…` | `yiiqcduiuz63c3vfr42xru2psv4aciep.dkim.amazonses.co…` |
| CNAME | `yppaohjblh5z4s…` | `yppaohjblh5z4sahkzr3pfgchsoticos.dkim.amazonses.co…` |
| TXT | `_dmarc` | `v=DMARC1; p=none;` |
| TXT | `_railway-verify.c…` | `railway-verify=004fd3af1893db2d2f2de15976cfc66ff5a…` |
| TXT | `hola` | `v=spf1 include:amazonses.com ~all` |
| TXT | `mailo._domaink…` | `k=rsa; p=MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBi…` |
| TXT | `resend._domain…` | `p=MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBg…` |
| TXT | `send` | `v=spf1 include:amazonses.com ~all` |
| URL Redirect | `ia.marionomics…` | `https://a.co/d/0eHwwkM6` (unmasked) |
| MX | `@` | `1 smtp.google.com.` (Mail Settings) |

GitHub Pages before: custom domain `blog.marionomics.com`, HTTPS enforced, source `gh-pages` branch.

**Rollback:** delete the four `185.199.*` A records, add back A `@` → `172.66.0.70` (TTL 5 min), and set `www` back to CNAME `marionomics.com.`.

**Carrd still serves `entrenamiento`, `guia` and `tesis`** — do not cancel the Carrd account until those are confirmed unused or moved.

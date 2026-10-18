"""What migrates to marionomics.com and where dropped Ghost pages should point (spec: Content scope)."""

SITE_URL = "https://marionomics.com"
SUBSTACK_URL = "https://marionomics.substack.com"
SUBSTACK_SUBSCRIBE_URL = "https://marionomics.substack.com/subscribe"

KEEP_PAGES = frozenset({"about", "about-2", "cv", "resena-curricular", "investigacion", "contacto"})

NOTION_50_RECURSOS = (
    "https://marionomics.notion.site/b7b39346e68d44f298f045c1a045eae7"
    "?v=edc6541f06cd4621a33049b93760e8ca"
)

# "/" means the landing page at the site root.
DROPPED_PAGE_TARGETS = {
    "signin": "/",
    "signup": "/",
    "bienvenida": "/",
    "bienvenida-a-premium": "/",
    "pro": "/",
    "econometria": "/",
    "cursos": "/",
    "cripto": "/",
    "consultoria": "/",
    "servicios": "/",
    "privacidad": "/",
    "condiciones": "/",
    "50-recursos-para-econometria": NOTION_50_RECURSOS,
}

# Old Ghost slugs that still appear in links, mapped to the post they now live at.
SLUG_ALIASES = {
    "quien-ganara-el-nobel-de-economia-2": "quien-ganara-el-nobel-de-economia",
}

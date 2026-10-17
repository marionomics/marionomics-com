from builders import ghost_data, ghost_post, write_export
from extract import Tag, load_export, select_items, used_tags


def test_load_export_reads_both_formats(tmp_path):
    data = ghost_data([ghost_post(slug="a")])
    for fmt in ("backup", "db"):
        assert load_export(write_export(tmp_path, data, fmt))["posts"][0]["slug"] == "a"


def test_select_items_keeps_published_posts_and_listed_pages():
    data = ghost_data([
        ghost_post(slug="post-ok"),
        ghost_post(slug="borrador", status="draft"),
        ghost_post(slug="enviado", status="sent"),
        ghost_post(slug="about-2", type="page"),
        ghost_post(slug="cripto", type="page"),
    ])
    items = select_items(data)
    assert {(i.slug, i.kind) for i in items} == {("post-ok", "post"), ("about-2", "page")}


def test_select_items_orders_newest_first():
    data = ghost_data([
        ghost_post(slug="viejo", published_at="2021-01-01T00:00:00.000Z"),
        ghost_post(slug="nuevo", published_at="2025-01-01T00:00:00.000Z"),
    ])
    assert [i.slug for i in select_items(data)] == ["nuevo", "viejo"]


def test_tags_are_public_only_and_in_sort_order():
    post = ghost_post(slug="p")
    data = ghost_data(
        [post],
        tags=[
            {"id": "t1", "slug": "python", "name": "Python", "visibility": "public"},
            {"id": "t2", "slug": "econometria", "name": "Econometría", "visibility": "public"},
            {"id": "t3", "slug": "hash-import", "name": "#Import 2023", "visibility": "internal"},
        ],
        posts_tags=[
            {"id": "x1", "post_id": post["id"], "tag_id": "t1", "sort_order": 1},
            {"id": "x2", "post_id": post["id"], "tag_id": "t2", "sort_order": 0},
            {"id": "x3", "post_id": post["id"], "tag_id": "t3", "sort_order": 2},
        ],
    )
    [item] = select_items(data)
    assert item.tags == [Tag("econometria", "Econometría"), Tag("python", "Python")]
    assert used_tags([item]) == [Tag("econometria", "Econometría"), Tag("python", "Python")]


def test_meta_fields_and_code_injection_are_joined():
    post = ghost_post(
        slug="p",
        codeinjection_head="<a>",
        codeinjection_foot="<b>",
        feature_image="__GHOST_URL__/content/images/x.png",
    )
    data = ghost_data([post], posts_meta=[{
        "id": "m", "post_id": post["id"], "meta_description": "Desc",
        "feature_image_alt": "Alt", "feature_image_caption": "<i>Cap</i>",
    }])
    [item] = select_items(data)
    assert (item.meta_description, item.feature_image_alt, item.feature_image_caption) == (
        "Desc", "Alt", "<i>Cap</i>")
    assert item.code_injection == "<a><b>"
    assert item.feature_image == "__GHOST_URL__/content/images/x.png"


def test_pages_never_carry_tags():
    page = ghost_post(slug="cv", type="page")
    data = ghost_data(
        [page],
        tags=[{"id": "t1", "slug": "python", "name": "Python", "visibility": "public"}],
        posts_tags=[{"id": "x1", "post_id": page["id"], "tag_id": "t1", "sort_order": 0}],
    )
    assert select_items(data)[0].tags == []

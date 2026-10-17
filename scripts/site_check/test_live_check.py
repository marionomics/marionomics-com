from live_check import check, old_paths


def test_old_paths_reads_first_column(tmp_path):
    redirects = tmp_path / "redirects.txt"
    redirects.write_text("/a/\thttps://marionomics.com/a/\n\n/tag/x/\thttps://marionomics.com/tag/x/\n")
    assert old_paths(redirects) == ["/a/", "/tag/x/"]


def test_check_reports_non_200_and_errors():
    responses = {"https://marionomics.com/a/": (200, "https://marionomics.com/a/"),
                 "https://marionomics.com/b/": (404, "https://marionomics.com/b/")}

    def fetch(url):
        if url not in responses:
            raise OSError("timeout")
        return responses[url]

    assert check(["/a/", "/b/", "/c/"], fetch, "https://marionomics.com") == [
        "/b/: 404",
        "/c/: error timeout",
    ]


def test_check_requires_ending_on_https_apex():
    responses = {"http://marionomics.com/a/": (200, "http://marionomics.com/a/"),
                 "http://marionomics.com/b/": (200, "https://marionomics.com/b/"),
                 "http://marionomics.com/c/": (200, "https://marionomics.com/")}

    assert check(["/a/", "/b/", "/c/"], responses.__getitem__, "http://marionomics.com") == [
        "/a/: ended at http://marionomics.com/a/",
        "/c/: ended at https://marionomics.com/",
    ]

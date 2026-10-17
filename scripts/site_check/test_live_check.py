from live_check import check, old_paths


def test_old_paths_reads_first_column(tmp_path):
    redirects = tmp_path / "redirects.txt"
    redirects.write_text("/a/\thttps://marionomics.com/a/\n\n/tag/x/\thttps://marionomics.com/tag/x/\n")
    assert old_paths(redirects) == ["/a/", "/tag/x/"]


def test_check_reports_non_200_and_errors():
    statuses = {"https://marionomics.com/a/": 200, "https://marionomics.com/b/": 404}

    def fetch(url):
        if url not in statuses:
            raise OSError("timeout")
        return statuses[url]

    assert check(["/a/", "/b/", "/c/"], fetch, "https://marionomics.com") == [
        "/b/: 404",
        "/c/: error timeout",
    ]

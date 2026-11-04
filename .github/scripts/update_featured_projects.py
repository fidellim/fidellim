"""Refresh the README showcase from public, owned repositories using GitHub CLI."""

import argparse
import html
import json
from pathlib import Path
import re
import subprocess
import textwrap

START = "<!--FEATURED_PROJECTS:start-->"
END = "<!--FEATURED_PROJECTS:end-->"


def cell(value):
    """Keep API text from introducing HTML, Markdown links, or table columns."""
    value = html.escape(" ".join((value or "").split()))
    return re.sub(r"([\\`*_\[\]|])", r"\\\1", value)


def build_section(repositories, username):
    eligible = [
        repo for repo in repositories
        if not repo["fork"] and not repo["private"]
        and repo["name"].casefold() != username.casefold()
    ]
    top = sorted(eligible, key=lambda repo: (-repo["stargazers_count"], repo["name"].casefold()))[:4]
    if len(top) < 4:
        raise ValueError("Expected at least four public original repositories; keeping the existing showcase.")
    lines = [
        "| Project | Stars | Language | About |",
        "| --- | ---: | --- | --- |",
    ]
    for repo in top:
        name = repo["name"]
        description = textwrap.shorten(repo.get("description") or "Explore the source code and project README.", width=160, placeholder="…")
        lines.append(
            f"| [{cell(name.replace('-', ' ').replace('_', ' '))}]"
            f"(https://github.com/{username}/{name}) | ⭐ {repo['stargazers_count']} "
            f"| {cell(repo.get('language') or '—')} | {cell(description)} |"
        )
    return "\n".join(lines)


def update_readme(path, section):
    content = path.read_text()
    if content.count(START) != 1 or content.count(END) != 1:
        raise ValueError("README must contain exactly one featured-project marker pair.")
    start = content.index(START) + len(START)
    end = content.index(END)
    if end < start:
        raise ValueError("Featured-project markers are out of order.")
    path.write_text(content[:start] + "\n\n" + section + "\n\n" + content[end:])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("username")
    args = parser.parse_args()
    response = subprocess.run(
        ["gh", "api", "--paginate", "--slurp", f"users/{args.username}/repos?per_page=100&type=owner"],
        check=True, capture_output=True, text=True,
    )
    repositories = [repo for page in json.loads(response.stdout) for repo in page]
    update_readme(Path("README.md"), build_section(repositories, args.username))


if __name__ == "__main__":
    main()

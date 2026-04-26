"""
GitHub Git Data API fixer for PR Security Auto-Fix.

The action validates exact search/replace patches before this module is called.
This module keeps the write path atomic: create blobs, build a tree, create one
commit, then move the PR branch ref forward without force-push.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Any

from github.Repository import Repository


@dataclass
class Patch:
    file: str
    search: str
    replace: str
    finding_id: str = ""
    reason: str = ""


def apply_to_contents(file_contents: dict[str, str], patches: list[Patch]) -> dict[str, str]:
    """Return modified file contents after applying exact unique patches."""
    patches_by_file: dict[str, list[Patch]] = {}
    for patch in patches:
        patches_by_file.setdefault(patch.file, []).append(patch)

    modified_contents: dict[str, str] = {}
    for filepath, file_patches in patches_by_file.items():
        content = file_contents[filepath]
        for patch in file_patches:
            count = content.count(patch.search)
            if count == 0:
                raise ValueError(f"Search string not found in {filepath}: {patch.search[:80]}...")
            if count > 1:
                raise ValueError(f"Search string ambiguous ({count} matches) in {filepath}: {patch.search[:80]}...")
            content = content.replace(patch.search, patch.replace, 1)
        modified_contents[filepath] = content
    return modified_contents


def apply_patches(
    repo: Repository,
    branch: str,
    base_sha: str,
    patches: list[Patch],
    file_contents: dict[str, str],
    commit_message: str,
) -> str:
    """Apply patches and commit to branch. Returns the new commit SHA."""
    modified_contents = apply_to_contents(file_contents, patches)

    if not modified_contents:
        raise ValueError("No files to patch")

    base_commit = repo.get_git_commit(base_sha)
    base_tree_sha = base_commit.tree.sha

    tree_elements: list[dict[str, Any]] = []
    for filepath, content in modified_contents.items():
        blob = repo.create_git_blob(
            content=base64.b64encode(content.encode("utf-8")).decode("ascii"),
            encoding="base64",
        )
        tree_elements.append({
            "path": filepath,
            "mode": "100644",
            "type": "blob",
            "sha": blob.sha,
        })

    from github.InputGitTreeElement import InputGitTreeElement

    tree_inputs = [
        InputGitTreeElement(
            path=el["path"],
            mode=el["mode"],
            type=el["type"],
            sha=el["sha"],
        )
        for el in tree_elements
    ]
    new_tree = repo.create_git_tree(tree_inputs, base_tree=repo.get_git_tree(base_tree_sha))

    new_commit = repo.create_git_commit(
        message=commit_message,
        tree=new_tree,
        parents=[base_commit],
    )

    ref = repo.get_git_ref(f"heads/{branch}")
    ref.edit(sha=new_commit.sha, force=False)

    return new_commit.sha

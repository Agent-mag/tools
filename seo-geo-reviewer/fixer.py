"""
GitHub Git Data API fixer — applies search/replace patches as a commit.

Uses the low-level Git Data API (create blob → create tree → create commit → update ref)
so we never need to clone or push. Works entirely via REST.

Safety:
- Only patches files matching PATCHABLE_PATTERNS (enforced in review.py)
- Each search string must match exactly once in the file
- If any patch fails validation, the entire commit is skipped
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


def apply_patches(
    repo: Repository,
    branch: str,
    base_sha: str,
    patches: list[Patch],
    file_contents: dict[str, str],
    commit_message: str,
) -> str:
    """
    Apply patches and commit to branch. Returns the new commit SHA.

    Algorithm:
    1. For each patch, apply search→replace to the in-memory file content.
    2. Create a blob for each modified file.
    3. Build a new tree with the updated blobs.
    4. Create a commit pointing to that tree.
    5. Update the branch ref to point to the new commit.
    """

    # Group patches by file — multiple patches can hit the same file
    patches_by_file: dict[str, list[Patch]] = {}
    for p in patches:
        patches_by_file.setdefault(p.file, []).append(p)

    # Apply patches in memory
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

    if not modified_contents:
        raise ValueError("No files to patch")

    # Get the base commit's tree
    base_commit = repo.get_git_commit(base_sha)
    base_tree_sha = base_commit.tree.sha

    # Create blobs for modified files
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

    # Create tree
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

    # Create commit
    new_commit = repo.create_git_commit(
        message=commit_message,
        tree=new_tree,
        parents=[base_commit],
    )

    # Update branch ref
    ref = repo.get_git_ref(f"heads/{branch}")
    ref.edit(sha=new_commit.sha, force=False)

    return new_commit.sha

#!/usr/bin/env python3
"""
Script to automatically generate documentation for pull requests and commits.
"""

import os
import sys
import datetime
import subprocess
from github import Github
from pathlib import Path

def get_git_info():
    """Get current git branch and commit information."""
    branch = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD']).decode('utf-8').strip()
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode('utf-8').strip()
    return branch, commit

def get_commit_details(commit_hash):
    """Get detailed information about a specific commit."""
    commit_msg = subprocess.check_output(['git', 'log', '--format=%B', '-n', '1', commit_hash]).decode('utf-8').strip()
    author = subprocess.check_output(['git', 'log', '--format=%an', '-n', '1', commit_hash]).decode('utf-8').strip()
    date = subprocess.check_output(['git', 'log', '--format=%ad', '-n', '1', commit_hash]).decode('utf-8').strip()
    return commit_msg, author, date

def get_changed_files(commit_hash):
    """Get list of files changed in the commit."""
    return subprocess.check_output(['git', 'diff-tree', '--no-commit-id', '--name-only', '-r', commit_hash]).decode('utf-8').split('\n')

def create_pr_documentation(pr_number, repo_name):
    """Create documentation for a specific pull request."""
    # Initialize Github client
    github_token = os.environ.get('GITHUB_TOKEN')
    if not github_token:
        print("Error: GITHUB_TOKEN environment variable not set")
        sys.exit(1)

    g = Github(github_token)
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(pr_number)

    # Create documentation directory if it doesn't exist
    doc_dir = Path('docs/pull_requests')
    doc_dir.mkdir(parents=True, exist_ok=True)

    # Generate documentation filename
    doc_file = doc_dir / f'PR_{pr_number}_{pr.title.replace(" ", "_")}.md'

    # Get PR details
    commits = list(pr.get_commits())
    changed_files = set()
    for commit in commits:
        changed_files.update(get_changed_files(commit.sha))

    # Create documentation content
    content = f"""# Pull Request #{pr_number}: {pr.title}

## Overview
- **Author**: {pr.user.login}
- **Created**: {pr.created_at}
- **Status**: {pr.state}
- **Branch**: {pr.head.ref} → {pr.base.ref}

## Description
{pr.body}

## Commits
"""

    # Add commit details
    for commit in commits:
        msg, author, date = get_commit_details(commit.sha)
        content += f"""
### Commit {commit.sha[:8]}
- **Author**: {author}
- **Date**: {date}
- **Message**: {msg}
"""

    # Add changed files
    content += "\n## Changed Files\n"
    for file in changed_files:
        if file:
            content += f"- {file}\n"

    # Add review status
    content += "\n## Reviews\n"
    reviews = pr.get_reviews()
    for review in reviews:
        content += f"- **{review.user.login}**: {review.state}\n"

    # Write documentation to file
    with open(doc_file, 'w') as f:
        f.write(content)

    return doc_file

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python pr_documentation.py <pr_number> <repo_name>")
        sys.exit(1)

    pr_number = int(sys.argv[1])
    repo_name = sys.argv[2]
    doc_file = create_pr_documentation(pr_number, repo_name)
    print(f"Documentation created: {doc_file}")
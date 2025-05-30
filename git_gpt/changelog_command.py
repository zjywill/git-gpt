from datetime import datetime
import click
import git
from .config_command import get_config
import os
from .ai_client import AIClient
from .git_diff import get_git_diff_by_commit_range

system_instruction = "You are going to work as a text generator, **you don't talk at all**, you will print your response in plain text without code block."

changelog_prompt = """
I have a `git diff` output from my recent code changes, and I need help with a changelog written in [insert_language].

## Changes
```diff
[insert_diff]
```

All notable changes to this project will be documented in this log.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Template:
```md
# Changelog

## [Version x.x.x] - [insert_date]

[write a detailed overview here.]

### Added(If applicable)
- [List new features that have been added.]
- [Include details about new modules, UI enhancements, etc.]

### Changed(If applicable)
- [Describe any changes to existing functionality.]
- [Note improvements, restructurings, or changes in behavior.]

### Deprecated(If applicable)
- [Document any features that are still available but are not recommended for use and will be removed in future versions.]

### Removed(If applicable)
- [List features or components that have been removed from this version.]

### Fixed(If applicable)
- [Highlight fixed bugs or issues.]
- [Include references to any tickets or bug report IDs if applicable.]

### Security(If applicable)
- [Mention any security improvements or vulnerabilities addressed in this version.]
```md
"""

@click.command()
@click.option('--lang', '-l', default=None, help='Target language for the generated changelog.')
@click.option('--model', '-m', default=None, help='The model to use for generating the changelog.')
@click.option('--max-tokens', '-t', type=int, help='The maximum number of tokens to use for the changelog.')
@click.option('--commit-range', '-r', type=int, help='The number of commits to include in the diff.')
def changelog(lang, model, max_tokens, commit_range):
    config = get_config()

    lang = lang or config.get('lang', 'English')
    model = model or config.get('default_model')

    if not model:
        raise ValueError("No default model specified in configuration. Please run git-gpt set-default to set default model or run git-gpt config to add model configuration.")

    diff = get_git_diff_by_commit_range(commit_range)

    max_tokens = max_tokens or config.get('changelog_max_tokens') or None

    ai_client = AIClient(config)

    try:
        click.echo(f"Generating changelog using {model} in {lang}...")

        prompt = changelog_prompt.replace('[insert_diff]', diff).replace('[insert_language]', lang).replace('[insert_date]', datetime.now().strftime('%Y-%m-%d'))

        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt}
        ]

        response = ai_client.request(messages=messages, model_alias=model, max_tokens=max_tokens)
        changelog_result = response
        click.echo(f"Changelog generated successfully:\n\n{changelog_result}")
    except ValueError as e:
        click.echo(f"Error: {str(e)}")
        click.echo("Please make sure you have set the API key using `git-gpt config --api-key <API_KEY>`")
    except Exception as e:
        click.echo(f"Error generating changelog: {str(e)}")
        click.echo("Please check the ai_client.py file for more details on the error.")

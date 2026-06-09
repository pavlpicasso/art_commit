# Commit Art

Python GitHub contribution art generator.

The project converts a 7 by 52 map into dated git commits. Rows are weekdays from Sunday to Saturday, columns are weeks. A space means no commits. The default non-empty intensity levels are `.`, `:`, `*`, and `#`.

## Quick Start

1. Install dependencies:

```bash
python -m pip install -e .
```

2. Edit `config.toml`:

```toml
origin = "https://github.com/your-name/commit-art.git"
branch = "master"
author_name = "Your Name"
author_email = "your_verified_github_email@example.com"
```

3. Generate a map from text:

```bash
python main.py text "HELLO" --level "#"
```

Copy the printed `map = [...]` block into `config.toml`.

4. Preview the result:

```bash
python main.py preview --year 2024 --visual --no-color
```

5. Check compatibility:

```bash
python main.py doctor --year 2024
```

6. Create local commits:

```bash
python main.py apply --year 2024 --reset-repo
```

7. Push when the generated repo looks right:

```bash
python main.py push
```

## Requirements

- Python 3.11+
- Git
- Pillow, used by image import
- GitHub CLI `gh`, only for `github-create`

Install project dependencies with:

```bash
python -m pip install -e .
```

## Configuration

Main settings live in `config.toml`.

```toml
origin = "https://github.com/your-name/commit-art.git"
branch = "master"
repo_dir = "repo"
commit_file = "commit_art.md"
timezone = "+0300"
commit_hour = 12
message_prefix = "Commit art"
author_name = "Commit Art"
author_email = "commit-art@example.com"

[levels]
"." = 4
":" = 8
"*" = 12
"#" = 20
```

Important fields:

- `origin`: GitHub repository URL or remote path.
- `branch`: branch that will receive generated commits.
- `repo_dir`: local directory where generated git history is created.
- `commit_file`: file changed by generated commits.
- `author_email`: must match a verified email on the target GitHub account.
- `[levels]`: map symbols and commit counts.

Use another config file with:

```bash
python main.py --config my-config.toml preview --year 2024
```

## Map Format

The contribution map is 7 rows by 52 columns:

- row 1: Sunday
- row 2: Monday
- row 3: Tuesday
- row 4: Wednesday
- row 5: Thursday
- row 6: Friday
- row 7: Saturday

Default symbols:

- space: no commits
- `.`: low intensity
- `:`: medium-low intensity
- `*`: medium-high intensity
- `#`: high intensity

## Date Modes

Default mode calculates dates from the Sunday of the week that was one year ago:

```bash
python main.py preview
```

Fixed-year mode draws into the 52-week grid containing January 1 of the requested year:

```bash
python main.py preview --year 2024
```

## Creating Maps

### From Text

```bash
python main.py text "HELLO"
python main.py text "2024" --level "*" --align left
python main.py text "DONE!" --level "#" --letter-spacing 0
```

Supported characters: `A-Z`, `0-9`, space, `-`, `_`, `!`, `?`, `.`.

The command prints a TOML `map = [...]` block. Paste it into `config.toml`.

### From Image

```bash
python main.py image assets/logo.png
python main.py image assets/logo.png --mode stretch
python main.py image assets/logo.png --mode cover --invert --preview
```

Dark pixels become higher contribution levels by default. Use `--invert` for light artwork on a dark background.

Image modes:

- `contain`: preserve aspect ratio and pad with empty cells.
- `cover`: preserve aspect ratio and crop to fill the grid.
- `stretch`: resize directly to 52 by 7.

Best source images are simple, high-contrast, and close to the 52:7 aspect ratio.

## Preview

List planned active days:

```bash
python main.py preview --year 2024 --limit 20
```

Render the contribution graph in the terminal:

```bash
python main.py preview --year 2024 --visual
python main.py preview --year 2024 --visual --no-color
```

`--no-color` is useful in terminals that show ANSI color codes as plain text.

## Validation And Doctor

Validate only the configured map:

```bash
python main.py validate
```

Run broader local compatibility checks:

```bash
python main.py doctor
python main.py doctor --year 2024
```

`doctor` checks:

- `git` availability;
- optional `gh` availability;
- config placeholders;
- map validity;
- `repo_dir` safety;
- local repo state;
- branch and origin;
- dirty working tree;
- author email shape;
- local commit count.

It does not call GitHub APIs. GitHub profile settings, verified emails, and default branch settings still need to be checked on GitHub.

## Applying Commits

Create commits locally:

```bash
python main.py apply --year 2024
```

Recreate `repo_dir` before applying:

```bash
python main.py apply --year 2024 --reset-repo
```

Append to an existing generated repository:

```bash
python main.py apply --year 2024 --allow-existing
```

Safety behavior:

- refuses to use the project root as `repo_dir`;
- refuses paths outside the workspace;
- refuses non-empty non-git directories;
- refuses existing git repositories without `--allow-existing`;
- refuses dirty repositories without `--allow-dirty`;
- never pushes from `apply`.

Inspect `repo_dir`:

```bash
python main.py repo-status
```

## Pushing

Push the generated repository:

```bash
python main.py push
```

Force push with lease:

```bash
python main.py push --force
```

Push very large histories in batches:

```bash
python main.py push --chunk-size 500 --chunk-delay 90
```

`push` refuses dirty repositories unless `--allow-dirty` is passed.

## GitHub Repository Helper

Create a GitHub repository with GitHub CLI:

```bash
python main.py github-create my-commit-art
python main.py github-create owner/my-commit-art --public --description "Contribution art"
python main.py github-create my-commit-art --no-source
python main.py github-create my-commit-art --push
```

By default this creates a private repository and attaches `repo_dir` as `gh --source` with remote `origin`.

## Script Generation

Instead of applying commits directly, generate a script:

```bash
python main.py generate-script --shell powershell
python main.py generate-script --shell bash
```

Generated scripts create local commits only. They do not push automatically.

## Testing

```bash
python -m unittest discover -s tests
```

## Implemented

- map validation;
- default rolling-year date calculation;
- fixed year selection with `--year`;
- external `config.toml`;
- 5 GitHub-style contribution levels;
- text-to-map generator;
- image-to-map importer;
- commit plan preview;
- visual terminal preview;
- GitHub contribution compatibility checks with `doctor`;
- bash and PowerShell script generation;
- direct local commit creation with `apply`;
- safe repo workflow with `repo-status`, path guards, dirty checks, and `--reset-repo`;
- push workflow with dirty checks, `--force-with-lease`, and chunked push;
- GitHub repository creation helper through `gh`.

# Commit Art

Python GitHub contribution art generator.

The project converts a 7 by 52 text map into dated commits. Rows are weekdays from Sunday to Saturday, columns are weeks. A space means no commits. The default intensity levels are `.`, `:`, `*`, and `#`.

## Commands

```bash
python main.py validate
python main.py preview
python main.py preview --visual
python main.py preview --visual --no-color
python main.py preview --year 2024
python main.py text "HELLO"
python main.py repo-status
python main.py apply --year 2024
python main.py apply --year 2024 --reset-repo
python main.py push
python main.py push --force
python main.py push --chunk-size 500
python main.py push --chunk-size 500 --chunk-delay 90
python main.py github-create my-commit-art --private
python main.py github-create owner/my-commit-art --public --description "Contribution art"
python main.py generate-script --shell powershell
python main.py generate-script --shell bash
python -m unittest discover -s tests
```

The generated script creates local commits in the current repository directory. It does not run `git push --force` automatically.

The `repo-status` command inspects the configured `repo_dir` before commits are created.

The `preview --visual` command renders the configured map as a 7 by 52 contribution graph in the terminal. Use `--no-color` for a plain text version.

The `apply` command creates commits directly in `repo_dir`. It creates the directory when it is missing, refuses to work in the project root, refuses paths outside the current workspace, and never pushes.

Existing repository options:

- `--allow-existing` appends commits to an existing git repository.
- `--allow-dirty` permits appending when that repository has uncommitted changes.
- `--reset-repo` deletes and recreates `repo_dir` before creating commits.

The `push` command pushes `repo_dir` to the configured `origin` and `branch`. It refuses to push a dirty repository unless `--allow-dirty` is passed. `--force` uses `--force-with-lease`.

Use `--chunk-size` to publish history progressively in smaller force-pushed batches. This can help GitHub process very large generated histories:

```bash
python main.py push --chunk-size 500 --chunk-delay 90
```

The `text` command renders text into a 7 by 52 map that can be pasted into `config.toml`:

```bash
python main.py text "HELLO" --level "#"
python main.py text "2024" --level "*" --align left
```

The `github-create` command wraps GitHub CLI `gh repo create`. By default it creates a private repository and attaches `repo_dir` as `--source` with remote `origin`:

```bash
python main.py github-create my-commit-art
python main.py github-create owner/my-commit-art --public --description "Contribution art"
python main.py github-create my-commit-art --no-source
python main.py github-create my-commit-art --push
```

By default, dates are calculated from the Sunday of the week that was one year ago. Use `--year` to draw into a fixed calendar-year grid. For example, `--year 2024` starts from the Sunday of the week containing January 1, 2024.

## Configuration

Edit `config.toml` to change the repository target, branch, generated file, timezone, commit levels, and the 7 by 52 map.

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

Use another config file with:

```bash
python main.py --config my-config.toml preview --year 2024
```

## Current Status

Implemented:

- map validation;
- default rolling-year date calculation;
- fixed year selection with `--year`;
- external `config.toml`;
- 5 GitHub-style contribution levels;
- text-to-map generator;
- commit plan preview;
- visual terminal preview;
- bash and PowerShell script generation.
- direct local commit creation with `apply`.
- safe repo workflow with `repo-status`, path guards, dirty checks, and `--reset-repo`.
- push workflow with dirty checks and `--force-with-lease`.
- GitHub repository creation helper through `gh`.

Next:

- image-to-map importer.

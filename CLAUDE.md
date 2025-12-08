# Claude Code Instructions

## Versioning

When making changes to this project, bump the version number appropriately:

- **Patch** (0.1.x): Bug fixes, minor improvements, new flags
- **Minor** (0.x.0): New features, significant changes
- **Major** (x.0.0): Breaking changes

Update version in both:
- `pyproject.toml` (line 3)
- `prepforinsta/__init__.py`

After committing, reinstall globally:
```bash
pipx install --force /Users/C4040588/code/prepforinsta
```

## Project Structure

- `prepforinsta/cli.py` - CLI interface (Click)
- `prepforinsta/processor.py` - Image processing logic (Pillow)
- `README.md` - User documentation

## Testing

Test changes with sample images before committing:
```bash
poetry run prepforinsta ~/test-images --max-size 6 -v
```

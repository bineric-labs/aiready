# llmstxt-generator

Generate `llms.txt` files for any website or local folder. Help AI agents understand your content.

## What is llms.txt?

[llms.txt](https://llmstxt.org/) is a proposed standard for helping LLMs understand your website. It's like `robots.txt`, but for AI.

## Features

- **Crawl any website** — Automatically discovers pages via sitemap or link following
- **Local folder support** — Point at a docs folder, get llms.txt
- **Path filtering** — Only include `/docs/*` or specific sections
- **Multiple output formats** — `llms.txt` and `llms-full.txt`
- **No paid crawling APIs** — Runs locally, you own your data

## Installation

```bash
pip install llmstxt-generator
```

Or run directly:

```bash
npx llmstxt-generator https://example.com
```

## Usage

### From a website

```bash
llmstxt https://docs.example.com
```

### From a local folder

```bash
llmstxt ./my-docs
```

### With options

```bash
llmstxt https://example.com \
  --include "/docs/*" \
  --exclude "/docs/archive/*" \
  --max-pages 50 \
  --output ./llms.txt
```

## Output

The tool generates two files:

**llms.txt** — Compact index with titles and descriptions:
```markdown
# Example Docs

> Documentation for Example product

## Guides

- [Getting Started](/docs/getting-started): Quick guide to set up Example in 5 minutes
- [Configuration](/docs/config): All configuration options explained
- [API Reference](/docs/api): Complete API documentation with examples
```

**llms-full.txt** — Full content for deeper context:
```markdown
# Example Docs

> Documentation for Example product

---

## Getting Started

Full content of the getting started page...

---

## Configuration

Full content of the configuration page...
```

## Configuration

Set your API key for AI-powered title/description generation:

```bash
export BINERIC_API_KEY=your-key-here
```

Or use a `.env` file:

```
BINERIC_API_KEY=your-key-here
```

**Get your API key at [bineric.com/platform](https://bineric.com/platform)**

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `BINERIC_API_KEY` | Your Bineric API key | (required for AI mode) |
| `BINERIC_API_URL` | API base URL | `https://api.bineric.com/v1` |
| `BINERIC_MODEL` | Model to use | `bineric-1` |

## How it works

1. **Discovery** — Finds all pages via sitemap.xml or by following links
2. **Extraction** — Pulls main content from each page (strips nav, footer, etc.)
3. **Summarization** — Uses AI to generate concise titles and descriptions
4. **Output** — Writes spec-compliant llms.txt and llms-full.txt

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `--include` | Only include paths matching pattern | `*` |
| `--exclude` | Exclude paths matching pattern | none |
| `--max-pages` | Maximum pages to process | 100 |
| `--output` | Output directory or file | `./llms.txt` |
| `--full` | Also generate llms-full.txt | true |
| `--no-ai` | Skip AI summarization, use page titles | false |

## License

MIT

## Credits

Built by [Bineric Labs](https://bineric.com)

Powered by [Bineric Platform](https://bineric.com/platform) - Privacy-focused AI

Inspired by [llms.txt](https://llmstxt.org/) by Answer.AI

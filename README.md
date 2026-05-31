# aiready

**Make your site AI ready.**

Generate `llms.txt` files so AI agents can discover and understand your website.

## What is this?

AI agents (ChatGPT, Claude, Perplexity, etc.) are browsing the web. `llms.txt` is a standard that helps them understand your site — like `sitemap.xml` for search engines, but for AI.

**aiready** crawls your site and generates this file automatically.

## Usage

```bash
aiready https://yoursite.com
```

Add your Bineric API key to generate AI-powered summaries:

```bash
aiready https://yoursite.com --api-key your-key-here
```

### Options

```bash
# Only include specific paths
aiready https://example.com --include "/docs/*"

# Exclude paths
aiready https://example.com --exclude "/blog/*"

# Limit pages
aiready https://example.com --max-pages 50

# Output to specific directory
aiready https://example.com --output ./output

# Use an API key for AI summaries
aiready https://example.com --api-key your-key-here

# Skip AI summarization (faster, uses page titles only)
aiready https://example.com --no-ai
```

### From a local folder

```bash
aiready ./my-docs
```

## Output

Successful runs generate two files:

**llms.txt** — Compact index for AI agents:
```markdown
# Your Site

> Brief description of your site

## Docs

- [Getting Started](/docs/start): Quick setup guide for new users
- [API Reference](/docs/api): Complete API documentation
```

**llms-full.txt** — Full content for deeper context.

## Configuration

For AI-powered summaries, pass your API key:

```bash
aiready https://yoursite.com --api-key your-key-here
```

Or set it once as an environment variable:

```bash
export BINERIC_API_KEY=your-key-here
```

Get your API key at [bineric.com/platform](https://bineric.com/platform)

| Variable | Description | Default |
|----------|-------------|---------|
| `BINERIC_API_KEY` | Your Bineric API key | (required for AI summaries) |
| `BINERIC_API_URL` | API base URL | `https://api.bineric.com/api/v1/ai` |

AI summaries always use `claude-sonnet-4.6`. Without an API key, aiready still runs and uses extracted page titles.

## Why llms.txt?

- **Be discovered** — AI agents will find and understand your site
- **Control the narrative** — You decide how AI describes you
- **Future-proof** — AI search is growing fast

## Learn more

- [llms.txt spec](https://llmstxt.org/) by Answer.AI

## License

MIT

---

Built by [Bineric](https://bineric.com)

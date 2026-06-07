# PerfEval
Latest deploy: http://63.176.178.150/

Prerquisities:
 - Installed Docker Desktop

## OpenAI API key setup

- Local/Docker: add `OPENAI_API_KEY=<your_key>` to [`.env`](.env)
- Optional: set `OPENAI_MODEL=gpt-4o-mini` in [`.env`](.env)
- GitHub Actions deploy: add repository secret `OPENAI_API_KEY`
  - Name: `OPENAI_API_KEY`
  - Value: your OpenAI API key

From infrastructure folder:

```
 docker compose up -d --build
```

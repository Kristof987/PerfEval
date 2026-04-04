# PerfEval
Latest deploy: http://63.176.178.150/

Prerquisities:
 - Installed Docker Desktop

## Gemini API key setup

- Local/Docker: add `GEMINI_API_KEY=<your_key>` to [`.env`](.env)
- GitHub Actions deploy: add repository secret `GEMINI_API_KEY`
  - Name: `GEMINI_API_KEY`
  - Value: your Gemini API key

From root:

```
 docker compose up -d --build
```

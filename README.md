# PerfEval
Latest deploy: http://63.176.178.150/

Prerquisities:
 - Installed Docker Desktop

## OpenAI API key setup

- Create `.env` file in root
- Add
  ```
  POSTGRES_DB=appdb
  POSTGRES_USER=appuser
  POSTGRES_PASSWORD=apppassword
  OPENAI_API_KEY=your-api-key
  ```

From infrastructure folder:

```
 docker compose up -d --build
```

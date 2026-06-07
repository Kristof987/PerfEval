# PerfEval
## Use deploy
Deploy is available here: http://63.176.178.150/

Available users:
- Test User -> a HR employee for HR related tasks
- Dev A -> normal employee
- Dev B -> normal employee
- etc.

## Run Locally
Repo link: https://github.com/Kristof987/PerfEval

Prerequisities:
 - Installed Docker Desktop

### OpenAI API key setup

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

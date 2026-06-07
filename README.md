# PerfEval
## Use the deployed app
The easiest way to try the app is the deployed version: http://63.176.178.150/

Available users:
- Test User -> a HR employee for HR related tasks
- Dev A -> normal employee
- Dev B -> normal employee
- etc.

## Run Locally
Repo link: https://github.com/Kristof987/PerfEval

Available users automatically:
- test_hr_user -> a HR employee for HR related tasks

Prerequisities:
 - Installed Docker Desktop

## Steps
1. Clone the repository

```
git clone https://github.com/Kristof987/PerfEval.git
cd PerfEval
```

2. Create .env and set OPENAI_API_KEY

- Create `.env` file in root
- Add
  ```
  POSTGRES_DB=appdb
  POSTGRES_USER=appuser
  POSTGRES_PASSWORD=apppassword
  OPENAI_API_KEY=your-api-key
```

3. Run the app

From infrastructure folder:

```
 docker compose up -d --build
```

# Example only - user must set real values
docker run --rm -p 8000:8000 `
  -e SECRET_KEY="__YOUR_SECRET__" `
  -e DEBUG="1" `
  -e ALLOWED_HOSTS="127.0.0.1,localhost" `
  -e SITE_BASE_URL="http://127.0.0.1:8000" `
  -e DB_NAME="__DB_NAME__" `
  -e DB_USER="__DB_USER__" `
  -e DB_PASSWORD="__DB_PASSWORD__" `
  -e DB_HOST="__DB_HOST__" `
  -e DB_PORT="3306" `
  newsapp:latest
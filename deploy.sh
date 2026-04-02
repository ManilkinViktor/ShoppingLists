#!/bin/bash

set -e

if [ -f .env.prod ]; then
    set -a
    source .env.prod
    set +a
else
    echo "Ошибка: .env.prod файл не найден!"
    exit 1
fi

echo "--- 1. Синхронизация файлов через rsync ---"

# Создаем директорию, если её нет
ssh "$SERVER_USER@$SERVER_IP" "mkdir -p $PROJECT_DIR"

# Передаем файлы, исключая лишнее
rsync -avz --delete \
    --exclude-from='.dockerignore' \
    --exclude='.env' \
    --exclude='.env.prod' \
    --exclude='.idea' \
    --exclude='.pylintrc' \
    --exclude='.git' \
    ./ "$SERVER_USER@$SERVER_IP:$PROJECT_DIR/"

echo "--- 2. Деплой на сервере ---"
ssh -T "$SERVER_USER@$SERVER_IP" << EOF
    cd "$PROJECT_DIR"
    docker compose -f docker-compose.prod.yml up -d --build
    docker image prune -f
EOF

echo "--- Готово ---"

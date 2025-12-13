# Pet DevOps Project

Этот проект демонстрирует полноценный CI/CD пайплайн с мониторингом и оркестрацией контейнеров. Цель проекта — создание автоматизированного процесса доставки приложений от разработки до продакшена с полной наблюдаемостью системы.

## Архитектура проекта
Git → Jenkins → Nexus → Docker → Kubernetes → Prometheus → Grafana

## Технологический стек

### CI/CD & Артефакты
- **Jenkins** — автоматизация CI/CD пайплайнов
- **Nexus Repository Manager 3** — хранение артефактов (Docker-образы, npm, PyPI)
- **Git** — контроль версий, хостинг на GitHub

### Контейнеризация и Оркестрация
- **Docker** — контейнеризация приложений
- **Kubernetes (Minikube)** — оркестрация контейнеров в локальном кластере
- **Helm** — управление Kubernetes-приложениями

### Мониторинг и Наблюдаемость
- **Prometheus** — сбор, хранение и запрос метрик
- **Grafana** — визуализация метрик и дашборды
- **kube-prometheus-stack** — комплексный стек мониторинга для Kubernetes
- **ServiceMonitor** — Custom Resource для автоматического обнаружения сервисов Prometheus

### Приложения
- **Backend** — Python Flask с REST API и эндпоинтом `/metrics` для Prometheus
- **Frontend** — React-приложение
- **PostgreSQL** — база данных в StatefulSet

## Реализованный мониторинг

### Архитектура сбора метрик
Flask Backend Pods (экспорт /metrics)
↓
Kubernetes Service: backend-metrics
↓ (обнаружение через селекторы)
ServiceMonitor: backend-explicit
↓ (конфигурация Prometheus)
Prometheus Server (сбор и хранение)
↓
[Grafana Dashboards] / [Prometheus UI] / [Alertmanager]

### Кастомные метрики Backend (Flask + `prometheus_client`)
- `http_requests_total` — счётчик HTTP-запросов с labels (`method`, `endpoint`, `status`)
- `http_request_duration_seconds` — гистограмма времени выполнения запросов
- Стандартные метрики Python (`python_gc_*`, `process_*`)

### Ключевые конфигурационные файлы
- `kubernetes/servicemonitor.yaml` — ServiceMonitor для автоматического обнаружения
- `backend/app.py` — Flask-приложение с эндпоинтом `/metrics`
- `backend/requirements.txt` — зависимости, включая `prometheus_client`

### Состояние системы
- **Prometheus Targets**: 2/3 пода бэкенда в состоянии **UP** (стабильная работа)
- **Метрики доступны** в Prometheus UI и через API
- **Алертинг**: настроены базовые правила через `PrometheusRule`

## Как проверить работоспособность мониторинга

### 1. Доступ к интерфейсам
```bash
# Prometheus UI (через порт-форвард с docker-host)
http://192.168.1.30:9090

# Проверить метрики бэкенда напрямую
curl http://localhost:8080/metrics | grep http_requests_total
2. Проверка в Prometheus UI
Откройте Status → Target Health — должен быть serviceMonitor/monitoring/backend-explicit/0 со статусом UP

В Graph выполните запросы:

http_requests_total — общее количество запросов
rate(http_requests_total[5m]) — интенсивность запросов
up{job="backend-metrics"} — состояние подов

3. Генерация тестового трафика
bash
# Создать нагрузку для проверки метрик
for i in {1..30}; do
  curl http://localhost:8080/health
  sleep 0.5
done

 Инфраструктура
Виртуальные машины и роли
VM	IP	Роль	Установленные компоненты
nexus	192.168.1.34	Хранилище артефактов	Nexus 3, Docker registry
jenkins-master	192.168.1.24	CI/CD сервер	Jenkins, Docker, Git
docker-host	192.168.1.30	Сборка и деплой	Docker, Minikube, kubectl, Helm, Grafana, Prometheus
Сетевые порты
Prometheus: 9090 (UI), 30090 (NodePort)

Grafana: 3000 (UI), 32092 (NodePort)

Backend: 5000 (приложение), 80 (сервис)

Nexus: 8081 (веб), 8083 (Docker registry)

🔧 Решённые проблемы и инсайты
1. Интеграция Prometheus с пользовательским приложением
Проблема: Prometheus не обнаруживал метрики бэкенда

Решение:
Добавлен эндпоинт /metrics в Flask-приложение с помощью prometheus_client
Создан ServiceMonitor с правильными селекторами и метками (release: monitoring)
Настроен namespaceSelector для обнаружения сервисов в namespace pet-project

2. Конфигурация ServiceMonitor
Проблема: Prometheus не применял конфигурацию ServiceMonitor
Решение:
ServiceMonitor должен находиться в том же namespace, что и Prometheus (monitoring)
Метки ServiceMonitor должны соответствовать селектору Prometheus (release: monitoring)
Имя порта в ServiceMonitor должно точно совпадать с именем порта в Kubernetes Service

3. Сетевая доступность
Проблема: NodePort сервисы Grafana/Prometheus недоступны с локальной машины
Решение: Использование kubectl port-forward для безопасного доступа к сервисам внутри кластера

4. Аутентификация Git на CI-сервере
Проблема: Ошибки аутентификации при push с docker-host
Решение:
Переход с пароля на Personal Access Token (PAT) GitHub

Проверка корректности URL удалённого репозитория

📁 Структура проекта
text
pet-project/
├── backend/                    # Flask приложение
│   ├── app.py                 # Основное приложение с метриками Prometheus
│   ├── requirements.txt       # Зависимости (Flask, prometheus_client)
│   └── Dockerfile            # Docker образ
├── frontend/                  # React приложение (в разработке)
├── kubernetes/               # Kubernetes манифесты
│   ├── deployment.yaml       # Деплоймент бэкенда
│   ├── service.yaml         # Сервисы
│   ├── servicemonitor.yaml  # ServiceMonitor для Prometheus
│   └── prometheus-rule.yaml # Правила алертов
├── Jenkinsfile               # CI/CD пайплайн
├── docker-compose.yml        # Локальный запуск
└── README.md                # Эта документация
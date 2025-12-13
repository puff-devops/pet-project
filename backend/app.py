from flask import Flask, jsonify, Response, request
import time
from prometheus_client import Counter, Histogram, generate_latest, REGISTRY, make_wsgi_app
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple

app = Flask(__name__)

# ========== PROMETHEUS METRICS ==========
# Счетчик HTTP запросов
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

# Гистограмма времени выполнения
REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['endpoint']
)

# ========== MIDDLEWARE ==========
@app.before_request
def before_request():
    """Засекаем время начала каждого запроса"""
    request.start_time = time.time()

@app.after_request
def after_request(response):
    """Собираем метрики после каждого запроса"""
    latency = time.time() - request.start_time
    
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.path,
        status=response.status_code
    ).inc()
    
    REQUEST_LATENCY.labels(
        endpoint=request.path
    ).observe(latency)
    
    return response

# ========== ROUTES ==========
@app.route('/health')
def health():
    """Health check для Kubernetes"""
    return jsonify({
        "status": "ok", 
        "service": "pet-backend",
        "timestamp": time.time()
    })

@app.route('/')
def home():
    """Главная страница"""
    return jsonify({
        "message": "Pet Project Backend API",
        "endpoints": ["/health", "/metrics", "/api/test"]
    })

@app.route('/api/test')
def test():
    """Тестовый endpoint для генерации трафика"""
    time.sleep(0.1) 
    return jsonify({"data": [1, 2, 3, 4, 5]})

@app.route('/metrics')
def metrics():
    """Endpoint для Prometheus"""
    from prometheus_client import generate_latest
    return Response(
        generate_latest(),
        mimetype='text/plain'
    )

# ========== MAIN ==========
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
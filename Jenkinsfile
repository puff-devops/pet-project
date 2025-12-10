pipeline {
    agent any

        environment {
        NEXUS_REGISTRY = '192.168.1.34:8083'
        DOCKER_CREDENTIALS_ID = 'nexus-docker-creds'
        GIT_CREDENTIALS_ID = 'github-creds'
        KUBE_CONFIG = credentials('kubeconfig')
        DOCKER_BUILDKIT = '1'
    }

    options {
        timeout(time: 30, unit: 'MINUTES')
        retry(2)
        buildDiscarder(logRotator(numToKeepStr: '10'))
        disableConcurrentBuilds()
    }

    stages {
        stage('Checkout') {
            steps {
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: '*/main']],
                    extensions: [],
                    userRemoteConfigs: [[
                        credentialsId: GIT_CREDENTIALS_ID,
                        url: 'https://github.com/puff-devops/pet-project.git'
                    ]]
                ])
            }
        }

        stage('Lint & Test') {
            parallel {
                stage('Backend Tests') {
                    steps {
                        dir('backend') {
                            sh '''
                                echo "Running Python tests..."
                                # Установка зависимостей перед тестами
                                python -m pip install -r requirements.txt || true
                                python -m pytest tests/ --junitxml=test-results.xml
                            '''
                        }
                    }
                    post {
                        always {
                            junit 'backend/test-results.xml'
                        }
                    }
                }
                stage('Frontend Lint') {
                    steps {
                        dir('frontend') {
                            sh '''
                                echo "Checking frontend code style..."
                                # Установка зависимостей перед проверкой
                                npm ci || npm install
                                npx eslint src/ --format junit --output-file eslint-results.xml
                            '''
                        }
                    }
                    post {
                        always {
                            junit 'frontend/eslint-results.xml'
                        }
                    }
                }
            }
        }

        stage('Build Docker Images') {
            steps {
                script {
                    dir('backend') {
                        docker.build("${NEXUS_REGISTRY}/pet-project/backend:${BUILD_ID}")
                    }
                    dir('frontend') {
                        docker.build("${NEXUS_REGISTRY}/pet-project/frontend:${BUILD_ID}")
                    }
                }
            }
        }

        stage('Security Scan') {
            steps {
                script {
                    sh """
                        docker scan ${NEXUS_REGISTRY}/pet-project/backend:${BUILD_ID} --file backend/Dockerfile || true
                        docker scan ${NEXUS_REGISTRY}/pet-project/frontend:${BUILD_ID} --file frontend/Dockerfile || true  // Исправлено: ${BUILD_ID} вместо {BUILD_ID}
                    """
                }
            }
        }

        stage('Push to Nexus') {
            steps {
                script {
                    docker.withRegistry("http://${NEXUS_REGISTRY}", DOCKER_CREDENTIALS_ID) {
                        docker.image("${NEXUS_REGISTRY}/pet-project/backend:${BUILD_ID}").push()
                        docker.image("${NEXUS_REGISTRY}/pet-project/frontend:${BUILD_ID}").push()
                        
                        docker.image("${NEXUS_REGISTRY}/pet-project/backend:${BUILD_ID}").push('latest')
                        docker.image("${NEXUS_REGISTRY}/pet-project/frontend:${BUILD_ID}").push('latest')
                    }
                }
            }
        }

        stage('Deploy to Minikube') {
            when {
                branch 'main'
            }
            steps {
                script {
                    writeFile file: 'kubeconfig.yaml', text: KUBE_CONFIG
                    
                    sh '''
                        # Используем отладочный вывод
                        sed -i "s|image:.*|image: ${NEXUS_REGISTRY}/pet-project/backend:${BUILD_ID}|g" kubernetes/backend-deployment.yaml
                        sed -i "s|image:.*|image: ${NEXUS_REGISTRY}/pet-project/frontend:${BUILD_ID}|g" kubernetes/frontend-deployment.yaml
                        
                        echo "Applying Kubernetes manifests..."
                        kubectl apply -f kubernetes/ -n pet-project --kubeconfig=kubeconfig.yaml
                        
                        echo "Waiting for deployments to be ready..."
                        kubectl rollout status deployment/backend -n pet-project --timeout=300s --kubeconfig=kubeconfig.yaml
                        kubectl rollout status deployment/frontend -n pet-project --timeout=300s --kubeconfig=kubeconfig.yaml
                    '''
                }
            }
        }

        stage('Smoke Tests') {
            when {
                branch 'main'
            }
            steps {
                script {
                    sh '''
                        # Получаем адрес сервиса
                        FRONTEND_URL=$(kubectl get svc frontend -n pet-project -o jsonpath="{.status.loadBalancer.ingress[0].ip}" --kubeconfig=kubeconfig.yaml)
                        
                        if [ -z "$FRONTEND_URL" ]; then
                            # Если нет external IP, используем port-forward
                            kubectl port-forward svc/frontend 8080:80 -n pet-project --kubeconfig=kubeconfig.yaml &
                            sleep 5
                            curl -f http://localhost:8080/health || exit 1
                        else
                            curl -f http://${FRONTEND_URL}/health --max-time 30 || exit 1
                        fi
                        
                        echo "Smoke test passed successfully"
                    '''
                }
            }
        }
    }
    
    post {
        success {
            echo '🎉 Pipeline успешно завершен!'
        }
        failure {
            echo '❌ Pipeline упал!'
        }
        unstable {
            echo '⚠️ Pipeline нестабилен (упали тесты)'
        }
        always {
            echo "Сборка #${BUILD_ID} завершена со статусом: ${currentBuild.result}"
            sh '''
                docker rmi ${NEXUS_REGISTRY}/pet-project/backend:${BUILD_ID} || true
                docker rmi ${NEXUS_REGISTRY}/pet-project/frontend:${BUILD_ID} || true
                docker rmi ${NEXUS_REGISTRY}/pet-project/backend:latest || true
                docker rmi ${NEXUS_REGISTRY}/pet-project/frontend:latest || true
            '''
            
            cleanWs()
            
            archiveArtifacts artifacts: '**/test-results.xml, **/eslint-results.xml', fingerprint: true
            
            archiveArtifacts artifacts: 'kubeconfig.yaml', fingerprint: false
        }
    }
}
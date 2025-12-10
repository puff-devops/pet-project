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

        stage('Build Docker Images') {
            steps {
                script {
                    // Backend
                    dir('backend') {
                        sh 'echo "Building backend image..."'
                        docker.build("${NEXUS_REGISTRY}/pet-project/backend:${BUILD_ID}")
                    }
                    // Frontend
                    dir('frontend') {
                        sh 'echo "Building frontend image..."'
                        docker.build("${NEXUS_REGISTRY}/pet-project/frontend:${BUILD_ID}")
                    }
                }
            }
        }

        stage('Push to Nexus') {
            steps {
                script {
                    docker.withRegistry("http://${NEXUS_REGISTRY}", DOCKER_CREDENTIALS_ID) {
                        docker.image("${NEXUS_REGISTRY}/pet-project/backend:${BUILD_ID}").push()
                        docker.image("${NEXUS_REGISTRY}/pet-project/frontend:${BUILD_ID}").push()
                    }
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
        always {
            echo "Сборка #${BUILD_ID} завершена"
            cleanWs()
        }
    }
}
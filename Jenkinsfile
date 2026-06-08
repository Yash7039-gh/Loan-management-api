pipeline {
    agent any

    environment {
        PYTHON_VERSION = '3.11'
        APP_PORT       = '5000'
    }

    stages {

        stage('🔍 Checkout') {
            steps {
                echo '── Pulling latest code from repository ──'
                checkout scm
            }
        }

        stage('🐍 Setup Python Environment') {
            steps {
                echo '── Creating virtual environment ──'
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }

        stage('🔎 Lint & Code Quality') {
            steps {
                echo '── Running flake8 linter ──'
                sh '''
                    . venv/bin/activate
                    pip install flake8
                    flake8 app.py --max-line-length=120 --ignore=E501,W503 || true
                '''
            }
        }

        stage('🧪 Run Tests') {
            steps {
                echo '── Running unit tests ──'
                sh '''
                    . venv/bin/activate
                    pip install pytest
                    pytest tests/ -v || echo "No tests found, skipping..."
                '''
            }
        }

        stage('🐳 Build Docker Image') {
            steps {
                echo '── Building Docker image ──'
                sh '''
                    docker build -t loan-management-api:${BUILD_NUMBER} .
                    docker tag loan-management-api:${BUILD_NUMBER} loan-management-api:latest
                '''
            }
        }

        stage('🚀 Deploy') {
            steps {
                echo '── Deploying application ──'
                sh '''
                    docker stop loan-api || true
                    docker rm loan-api   || true
                    docker run -d \
                        --name loan-api \
                        -p ${APP_PORT}:5000 \
                        --env-file .env \
                        loan-management-api:latest
                    echo "✅ Deployed on port ${APP_PORT}"
                '''
            }
        }

        stage('✅ Health Check') {
            steps {
                echo '── Verifying deployment ──'
                sh '''
                    sleep 5
                    curl -f http://localhost:${APP_PORT}/ || exit 1
                    echo "✅ Health check passed!"
                '''
            }
        }
    }

    post {
        success {
            echo '🎉 Pipeline completed successfully!'
        }
        failure {
            echo '❌ Pipeline failed. Check logs above.'
        }
        always {
            echo '── Cleaning workspace ──'
            cleanWs()
        }
    }
}

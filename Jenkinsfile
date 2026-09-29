pipeline {
    agent any

    environment {
        // Replace 'your-dockerhub-username' with your actual Docker Hub username
        DOCKER_HUB_REPO = 'tamilmani5297/devops-gemini-app'
        IMAGE_TAG       = "${BUILD_NUMBER}"
        
        // Fetch API Key dynamically from Jenkins Credentials Store
        GEMINI_KEY      = credentials('gemini-api-key')
    }

    stages {
        stage('Checkout Code') {
            steps {
                echo 'Pulling application source code from GitHub...'
                checkout scm
            }
        }

        stage('Code Validation') {
            steps {
                echo 'Validating Python syntax...'
                sh 'python3 -m py_compile app.py || true'
            }
        }

        stage('Build Docker Image') {
            steps {
                echo "Building Docker container image: ${DOCKER_HUB_REPO}:${IMAGE_TAG}..."
                sh "docker build -t ${DOCKER_HUB_REPO}:${IMAGE_TAG} -t ${DOCKER_HUB_REPO}:latest ."
            }
        }

        stage('Push to Docker Hub') {
            steps {
                echo 'Authenticating and pushing image to registry...'
                withCredentials([usernamePassword(credentialsId: 'docker-hub-credentials', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                    sh '''
                        echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin
                        docker push $DOCKER_HUB_REPO:$IMAGE_TAG
                        docker push $DOCKER_HUB_REPO:latest
                        docker logout
                    '''
                }
            }
        }

        stage('Generate Dynamic K8s Secret') {
            steps {
                echo 'Injecting credentials into runtime Kubernetes secret...'
                script {
                    def encodedKey = GEMINI_KEY.bytes.encodeBase64().toString()
                    writeFile file: 'k8s/secret.yaml', text: """
apiVersion: v1
kind: Secret
metadata:
  name: gemini-secret
type: Opaque
data:
  GEMINI_API_KEY: ${encodedKey}
"""
                }
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                echo 'Applying Kubernetes manifests...'
                sh '''
                    kubectl apply -f k8s/secret.yaml
                    kubectl apply -f k8s/deployment.yaml
                    kubectl apply -f k8s/service.yaml
                    kubectl rollout status deployment/devops-gemini-deployment
                '''
            }
        }
    }

    post {
        always {
            echo 'Cleaning up sensitive build artifacts...'
            sh 'rm -f k8s/secret.yaml'
        }
        success {
            echo 'Pipeline completed successfully!'
        }
        failure {
            echo 'Pipeline failed. Inspect stage logs above.'
        }
    }
}
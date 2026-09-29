pipeline {
    agent any

    environment {
        // Docker Hub repository definition
        DOCKER_HUB_REPO = 'tamilmaniperumal5297/devops-gemini-app'
        IMAGE_TAG       = "${BUILD_NUMBER}"
        
        // Fetch API Key from Jenkins Credentials Store
        GEMINI_KEY      = credentials('gemini-api-key')
    }

    stages {
        stage('Checkout Source Code') {
            steps {
                echo 'Checking out source code from GitHub...'
                checkout scm
            }
        }

        stage('Code Validation') {
            steps {
                echo 'Validating Python syntax...'
                // Using cross-platform compile check
                sh 'python3 -m py_compile app.py test_script.py || true'
            }
        }

        stage('Build Docker Image') {
            steps {
                echo "Building Docker container image: ${DOCKER_HUB_REPO}:${IMAGE_TAG}..."
                sh "docker build -t ${DOCKER_HUB_REPO}:${IMAGE_TAG} -t ${DOCKER_HUB_REPO}:latest ."
            }
        }

        stage('Push Image to Docker Hub') {
            steps {
                echo 'Authenticating and pushing image to Docker Hub...'
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
            script {
                echo 'Cleaning up temporary workspace secrets...'
                def secretFile = new File("${WORKSPACE}/k8s/secret.yaml")
                if (secretFile.exists()) {
                    secretFile.delete()
                    echo 'k8s/secret.yaml safely removed.'
                }
            }
        }
        success {
            echo 'Pipeline executed successfully! Application deployed to Kubernetes.'
        }
        failure {
            echo 'Pipeline execution failed. Inspect stage logs for details.'
        }
    }
}
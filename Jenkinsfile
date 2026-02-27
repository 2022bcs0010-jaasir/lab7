pipeline {
    agent any

    environment {
        DOCKER_IMAGE   = "mdjaasir2022bcs0010/lab7"
        METRICS_FILE   = "app/artifacts/metrics.json"
        CONTAINER_NAME = "wine_validation_container"
        PORT           = "8002"
    }

    stages {

        // ===============================
        // LAB 6 - TRAINING PIPELINE
        // ===============================

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Setup Python Virtual Environment') {
            steps {
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }

        stage('Train Model') {
            steps {
                sh '''
                    . venv/bin/activate
                    python train.py
                '''
            }
        }

        stage('Read Metrics') {
            steps {
                script {
                    def metrics = readJSON file: "${METRICS_FILE}"
                    env.CURRENT_MSE = metrics.MSE.toString()
                    env.CURRENT_R2  = metrics.R2.toString()

                    echo "Current MSE: ${env.CURRENT_MSE}"
                    echo "Current R2 : ${env.CURRENT_R2}"
                }
            }
        }

        stage('Compare Metrics') {
            steps {
                script {
                    withCredentials([
                        string(credentialsId: 'BEST_MSE', variable: 'BEST_MSE'),
                        string(credentialsId: 'BEST_R2', variable: 'BEST_R2')
                    ]) {

                        def current_mse = env.CURRENT_MSE.toFloat()
                        def current_r2  = env.CURRENT_R2.toFloat()

                        def best_mse = BEST_MSE.toFloat()
                        def best_r2  = BEST_R2.toFloat()

                        echo "Best MSE: ${best_mse}"
                        echo "Best R2 : ${best_r2}"

                        if (!(current_mse < best_mse && current_r2 > best_r2)) {
                            error("Model did NOT improve. Stopping pipeline.")
                        }

                        echo "Model Improved. Proceeding to build."
                    }
                }
            }
        }

        // ===============================
        // BUILD & PUSH
        // ===============================

        stage('Build Docker Image') {
            steps {
                sh 'docker build -t ${DOCKER_IMAGE}:${BUILD_NUMBER} .'
            }
        }

        stage('Push Docker Image') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'docker-access',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh '''
                        echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin
                        docker tag ${DOCKER_IMAGE}:${BUILD_NUMBER} ${DOCKER_IMAGE}:latest
                        docker push ${DOCKER_IMAGE}:${BUILD_NUMBER}
                        docker push ${DOCKER_IMAGE}:latest
                    '''
                }
            }
        }

        // ===============================
        // LAB 7 - VALIDATION PIPELINE
        // ===============================

        stage('Pull Docker Image') {
            steps {
                sh 'docker pull ${DOCKER_IMAGE}:latest'
            }
        }

        stage('Run Container') {
            steps {
                sh '''
                    docker run -d -p ${PORT}:8000 \
                    --name ${CONTAINER_NAME} \
                    ${DOCKER_IMAGE}:latest
                '''
            }
        }

        stage('Wait for API Readiness') {
            steps {
                script {
                    timeout(time: 60, unit: 'SECONDS') {
                        waitUntil {
                            def status = sh(
                                script: "curl -s -o /dev/null -w '%{http_code}' http://host.docker.internal:${PORT}/health || true",
                                returnStdout: true
                            ).trim()
                            return status == "200"
                        }
                    }
                }
            }
        }

        stage('Valid Inference Test') {
            steps {
                script {
                    def status = sh(
                        script: """
                        curl -s -o valid.txt -w '%{http_code}' \
                        -X POST http://localhost:${PORT}/predict \
                        -H "Content-Type: application/json" \
                        -d '{
                          "fixed_acidity": 7.4,
                          "volatile_acidity": 0.7,
                          "citric_acid": 0.0,
                          "residual_sugar": 1.9,
                          "chlorides": 0.076,
                          "free_sulfur_dioxide": 11.0,
                          "total_sulfur_dioxide": 34.0,
                          "density": 0.9978,
                          "pH": 3.51,
                          "sulphates": 0.56,
                          "alcohol": 9.4
                        }'
                        """,
                        returnStdout: true
                    ).trim()

                    def response = readFile('valid.txt')
                    echo "Valid Response: ${response}"

                    if (status != "200") {
                        error("Valid request failed (HTTP error)")
                    }

                    if (!response.contains("prediction")) {
                        error("Prediction field missing in response")
                    }

                    echo "Valid inference test passed."
                }
            }
        }

        stage('Invalid Inference Test') {
            steps {
                script {
                    def status = sh(
                        script: """
                        curl -s -o invalid.txt -w '%{http_code}' \
                        -X POST http://localhost:${PORT}/predict \
                        -H "Content-Type: application/json" \
                        -d '{"fixed_acidity": 7.4}'
                        """,
                        returnStdout: true
                    ).trim()

                    def response = readFile('invalid.txt')
                    echo "Invalid Response: ${response}"

                    if (status == "200") {
                        error("Invalid request should NOT succeed")
                    }

                    echo "Invalid inference test passed."
                }
            }
        }
    }

    // ===============================
    // POST ACTIONS
    // ===============================

    post {

        always {
            sh "docker rm -f ${CONTAINER_NAME} || true"
            archiveArtifacts artifacts: 'app/artifacts/**', fingerprint: true
        }

        success {
            echo "PIPELINE SUCCESS: Model trained, deployed, and validated successfully."
        }

        failure {
            echo "PIPELINE FAILED: Training or validation step failed."
        }
    }
}
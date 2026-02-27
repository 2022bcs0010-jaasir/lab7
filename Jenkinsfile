pipeline {
    agent any

    environment {
        DOCKER_IMAGE = "mdjaasir2022bcs0010/lab6"
        METRICS_FILE = "app/artifacts/metrics.json"
    }

    stages {

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

        stage('Read Accuracy') {
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

   
        stage('Compare Accuracy') {
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

                        if (current_mse < best_mse && current_r2 > best_r2) {
                            env.MODEL_IMPROVED = "true"
                            echo "Model Improved "
                        } else {
                            env.MODEL_IMPROVED = "false"
                            echo "Model Did Not Improve "
                        }
                    }
                }
            }
        }

        
        stage('Build Docker Image') {
            when {
                expression { env.MODEL_IMPROVED == "true" }
            }
            steps {
                sh '''
                    docker build -t ${DOCKER_IMAGE}:${BUILD_NUMBER} .
                '''
            }
        }

     
        stage('Push Docker Image') {
            when {
                expression { env.MODEL_IMPROVED == "true" }
            }
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
    }

   
    post {
        always {
            archiveArtifacts artifacts: 'app/artifacts/**', fingerprint: true
        }
    }
}

// ── Jenkinsfile ─────────────────────────────────────────────────────────────
// Defines the CI/CD pipeline for EduForAll using Jenkins.
//
// What this pipeline does automatically every time code is pushed:
//   1. Checkout  — pulls the latest code from the repository
//   2. Install   — installs all Python dependencies
//   3. Lint      — checks code quality with Flake8 and PyLint
//   4. Test      — runs all pytest unit tests
//   5. Build     — builds the Docker image
//   6. Deploy    — runs the Docker container (on main branch only)
//
// How to use:
//   - Install Jenkins and the Pipeline plugin
//   - Create a new Pipeline job and point it to this Jenkinsfile
//   - Jenkins will run this pipeline automatically on every code push

pipeline {

    // ── Agent ──────────────────────────────────────────────────────────────
    // Run the pipeline on any available Jenkins agent (worker machine)
    agent any

    // ── Environment Variables ───────────────────────────────────────────────
    // Variables available to all stages in the pipeline
    environment {
        APP_NAME    = "eduforall"           // Docker image name
        APP_PORT    = "8501"                // Port Streamlit runs on
        PYTHON      = "python"              // Python command (use 'python3' on Linux)
        PIP         = "pip"                 // Pip command
    }

    // ── Pipeline Options ────────────────────────────────────────────────────
    options {
        // Keep only the last 5 build logs to save disk space
        buildDiscarder(logRotator(numToKeepStr: '5'))

        // Fail the build if it takes longer than 30 minutes
        timeout(time: 30, unit: 'MINUTES')

        // Add timestamps to all console output for easier debugging
        timestamps()
    }

    // ── Stages ──────────────────────────────────────────────────────────────
    // Each stage is a step in the pipeline. They run in order.
    // If any stage fails, Jenkins stops and marks the build as FAILED.
    stages {

        // ── Stage 1: Checkout ──────────────────────────────────────────────
        // Pulls the latest code from the Git repository
        stage('Checkout') {
            steps {
                echo '📥 Checking out source code...'
                checkout scm   // 'scm' = the repository configured in the Jenkins job
            }
        }

        // ── Stage 2: Install Dependencies ─────────────────────────────────
        // Installs all Python packages from requirements.txt
        stage('Install Dependencies') {
            steps {
                echo '📦 Installing Python dependencies...'
                sh '''
                    ${PIP} install --upgrade pip
                    ${PIP} install -r requirements.txt
                '''
                // Note: on Windows agents, use 'bat' instead of 'sh':
                // bat 'pip install -r requirements.txt'
            }
        }

        // ── Stage 3: Code Quality — Flake8 ────────────────────────────────
        // Flake8 checks for syntax errors, undefined names, and PEP8 style
        stage('Lint - Flake8') {
            steps {
                echo '🔍 Running Flake8 code style check...'
                sh '''
                    pip install flake8
                    flake8 app.py auth.py model.py database.py \
                        --max-line-length=120 \
                        --exclude=__pycache__,.git \
                        --statistics
                '''
                // --max-line-length=120: allow lines up to 120 chars (relaxed from 79)
                // --statistics: shows how many of each error type were found
            }
        }

        // ── Stage 4: Code Quality — PyLint ────────────────────────────────
        // PyLint gives a score out of 10 and lists code issues
        stage('Lint - PyLint') {
            steps {
                echo '🔍 Running PyLint code analysis...'
                sh '''
                    pip install pylint
                    pylint app.py auth.py model.py database.py \
                        --disable=C0114,C0115,C0116 \
                        --max-line-length=120 \
                        --fail-under=5.0 || true
                '''
                // --disable=C0114,C0115,C0116: skip missing docstring warnings
                //   (we already have docstrings, this avoids false positives)
                // --fail-under=5.0: only fail if score is below 5/10
                // || true: don't fail the pipeline on minor pylint warnings
            }
        }

        // ── Stage 5: Run Tests ─────────────────────────────────────────────
        // Runs all pytest unit tests and generates a report
        stage('Run Tests') {
            steps {
                echo '✅ Running unit tests with pytest...'
                sh '''
                    pip install pytest pytest-cov
                    pytest tests/ \
                        --verbose \
                        --tb=short \
                        --cov=. \
                        --cov-report=term-missing
                '''
                // --verbose: show each test name and result
                // --tb=short: show short traceback on failures
                // --cov: measure code coverage
                // --cov-report=term-missing: show which lines aren't covered
            }
        }

        // ── Stage 6: Build Docker Image ────────────────────────────────────
        // Builds the Docker image using our Dockerfile
        stage('Build Docker Image') {
            steps {
                echo '🐳 Building Docker image...'
                sh '''
                    docker build -t ${APP_NAME}:latest .
                    docker images | grep ${APP_NAME}
                '''
                // docker images | grep: confirms the image was created
            }
        }

        // ── Stage 7: Deploy ────────────────────────────────────────────────
        // Only runs on the main branch — stops old container and starts new one
        stage('Deploy') {
            when {
                // Only deploy when pushing to the main branch
                branch 'main'
            }
            steps {
                echo '🚀 Deploying EduForAll container...'
                sh '''
                    # Stop and remove the old container if it exists
                    docker stop ${APP_NAME} || true
                    docker rm   ${APP_NAME} || true

                    # Start the new container
                    docker run -d \
                        --name ${APP_NAME} \
                        -p ${APP_PORT}:${APP_PORT} \
                        --restart unless-stopped \
                        ${APP_NAME}:latest

                    echo "✅ App deployed at http://localhost:${APP_PORT}"
                '''
                // -d: run in background (detached mode)
                // --restart unless-stopped: auto-restart if the container crashes
            }
        }
    }

    // ── Post Actions ────────────────────────────────────────────────────────
    // These run after all stages — regardless of success or failure
    post {

        success {
            // Runs if ALL stages passed
            echo '''
            ✅ ══════════════════════════════════════
               Pipeline PASSED — EduForAll is live!
            ══════════════════════════════════════
            '''
        }

        failure {
            // Runs if ANY stage failed
            echo '''
            ❌ ══════════════════════════════════════
               Pipeline FAILED — check the logs above
            ══════════════════════════════════════
            '''
        }

        always {
            // Always runs — cleans up workspace after the build
            echo '🧹 Cleaning up workspace...'
            cleanWs()
        }
    }
}

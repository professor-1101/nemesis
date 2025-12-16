#!/bin/bash
# Script to run SonarQube analysis for Nemesis

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

echo "🔍 Starting SonarQube analysis for Nemesis..."

# Check if sonar-scanner is installed
if ! command -v sonar-scanner &> /dev/null; then
    echo "❌ sonar-scanner not found!"
    echo "Please install it from: https://docs.sonarqube.org/latest/analyzing-source-code/scanners/sonarscanner/"
    exit 1
fi

# Check for SonarCloud token
if [ -z "$SONAR_TOKEN" ]; then
    echo "⚠️  SONAR_TOKEN not set. Using sonar-project.properties settings."
    echo "For SonarCloud, set: export SONAR_TOKEN=your_token"
fi

# Run analysis
sonar-scanner

echo "✅ Analysis complete! Check SonarQube/SonarCloud dashboard."


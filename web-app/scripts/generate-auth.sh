#!/bin/bash

# Script to generate Traefik dashboard authentication
# Usage: ./scripts/generate-auth.sh username password

if [ $# -ne 2 ]; then
    echo "Usage: $0 <username> <password>"
    echo "Example: $0 admin mypassword"
    exit 1
fi

USERNAME=$1
PASSWORD=$2

# Check if htpasswd is available
if ! command -v htpasswd &> /dev/null; then
    echo "htpasswd is not installed. Installing apache2-utils..."
    
    # Detect OS and install htpasswd
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command -v apt-get &> /dev/null; then
            sudo apt-get update && sudo apt-get install -y apache2-utils
        elif command -v yum &> /dev/null; then
            sudo yum install -y httpd-tools
        elif command -v dnf &> /dev/null; then
            sudo dnf install -y httpd-tools
        else
            echo "Please install htpasswd manually"
            exit 1
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        if command -v brew &> /dev/null; then
            brew install httpd
        else
            echo "Please install htpasswd manually or install Homebrew"
            exit 1
        fi
    else
        echo "Unsupported OS. Please install htpasswd manually"
        exit 1
    fi
fi

# Generate the auth string
AUTH_STRING=$(echo $(htpasswd -nb $USERNAME $PASSWORD) | sed -e s/\\$/\\$\\$/g)

echo "Generated authentication string:"
echo "TRAEFIK_AUTH=$AUTH_STRING"
echo ""
echo "Add this to your .env.https file"
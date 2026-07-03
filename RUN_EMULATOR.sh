#!/bin/bash

# Echo V4 - Emulator Run Script
# Quick commands to run the app on Android emulator

echo "🚀 Echo V4 Emulator Launcher"
echo "=============================="
echo ""

# Set Flutter path
export PATH="$HOME/flutter/bin:$PATH"

# Navigate to project
cd /home/jacob/Desktop/Goeckoh_Mobile_Master

echo "📱 Starting Android Emulator..."
flutter emulators --launch Medium_Phone_API_36 &

echo "⏳ Waiting for emulator to boot (30 seconds)..."
sleep 30

echo "🏗️  Building and running app..."
flutter run

# If the above doesn't work, try:
# flutter run -d emulator-5554

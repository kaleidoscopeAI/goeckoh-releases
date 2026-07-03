#!/bin/bash

# Echo V4 Production Build Script
# This script builds the app for different platforms

set -e  # Exit on error

echo "🚀 Echo V4 Production Build Script"
echo "=================================="

# Check Flutter installation
if ! command -v flutter &> /dev/null; then
    echo "❌ Flutter not found. Please install Flutter first."
    exit 1
fi

echo "✅ Flutter found: $(flutter --version | head -1)"

# Clean previous builds
echo ""
echo "🧹 Cleaning previous builds..."
flutter clean
flutter pub get

# Function to build Android
build_android() {
    echo ""
    echo "📱 Building Android APK..."
    flutter build apk --release --split-per-abi
    
    if [ $? -eq 0 ]; then
        echo "✅ Android APK built successfully!"
        echo "📦 APK location: build/app/outputs/flutter-apk/"
        ls -lh build/app/outputs/flutter-apk/*.apk
    else
        echo "❌ Android build failed"
        exit 1
    fi
}

# Function to build Android App Bundle
build_android_bundle() {
    echo ""
    echo "📱 Building Android App Bundle (for Play Store)..."
    flutter build appbundle --release
    
    if [ $? -eq 0 ]; then
        echo "✅ Android App Bundle built successfully!"
        echo "📦 AAB location: build/app/outputs/bundle/release/"
        ls -lh build/app/outputs/bundle/release/*.aab
    else
        echo "❌ Android App Bundle build failed"
        exit 1
    fi
}

# Function to build iOS
build_ios() {
    if [[ "$OSTYPE" != "darwin"* ]]; then
        echo "⚠️  iOS builds require macOS"
        return
    fi
    
    echo ""
    echo "🍎 Building iOS..."
    flutter build ios --release --no-codesign
    
    if [ $? -eq 0 ]; then
        echo "✅ iOS build successful!"
        echo "📦 Build location: build/ios/iphoneos/"
    else
        echo "❌ iOS build failed"
        exit 1
    fi
}

# Function to build Web
build_web() {
    echo ""
    echo "🌐 Building Web (Demo Mode)..."
    flutter build web --release
    
    if [ $? -eq 0 ]; then
        echo "✅ Web build successful!"
        echo "📦 Web files: build/web/"
        echo "ℹ️  Note: Web version runs in demo mode (no local AI)"
    else
        echo "❌ Web build failed"
        exit 1
    fi
}

# Main menu
echo ""
echo "Select build target:"
echo "1) Android APK"
echo "2) Android App Bundle (Play Store)"
echo "3) iOS (macOS only)"
echo "4) Web"
echo "5) All platforms"
echo "6) Exit"
echo ""
read -p "Enter choice [1-6]: " choice

case $choice in
    1)
        build_android
        ;;
    2)
        build_android_bundle
        ;;
    3)
        build_ios
        ;;
    4)
        build_web
        ;;
    5)
        build_android
        build_android_bundle
        build_ios
        build_web
        ;;
    6)
        echo "👋 Exiting..."
        exit 0
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "✅ Build process completed!"
echo ""
echo "📝 Next steps:"
echo "  • Test the build on a device"
echo "  • Check app size and performance"
echo "  • Run through QA checklist"
echo "=================================="

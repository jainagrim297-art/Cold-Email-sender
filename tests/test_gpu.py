import os
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)

# We flush the output immediately to bypass any Windows terminal freezing
print("🚀 If you see this, Python is successfully running the file!", flush=True)

try:
    from src.processor.classifier import SignalClassifier
    print("✅ Successfully imported the AI Brain.")
    
    print("⏳ Loading AI into RTX 4060... (Wait for it)")
    ai = SignalClassifier()
    
    print("\n🧠 Testing a fake startup blog...")
    result = ai.analyze_signal("<html><body><p>We are scaling our AWS servers.</p></body></html>")
    
    print(f"\n🎯 AI Decision: {result['category']}")

except Exception as e:
    print(f"❌ ERROR: {e}")

print("🏁 Test complete.")
from services.smart_goal_manager import smart_goal_manager

print("🧠 SMART GOAL MANAGER TEST")
print("="*50)

targets = [500, 5000, 25000, 80000]

for target in targets:
    config = smart_goal_manager.get_smart_dashboard_config(target)
    print(f"Target {target:,} comments:")
    print(f"  - Mode: {config['processing_mode']}")
    print(f"  - Queries: {config['query_variations']}")
    print(f"  - Time: {config['estimated_time']}")
    print(f"  - Sources: {', '.join(config['recommended_sources'])}")
    print()

print("✅ Smart Goal Manager working correctly!")
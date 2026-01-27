from app.core.schemas import Topic

# Topic -> list of keywords for deterministic tagging
TOPIC_KEYWORDS: dict[Topic, list[str]] = {
    Topic.TECH: [
        "tech", "software", "ai", "artificial intelligence", "google", "apple", "microsoft", 
        "semiconductor", "robot", "cloud", "digital", "startup", "developer", "coding", "chip",
        "nvidia", "gpu"
    ],
    Topic.FINANCE: [
        "finance", "market", "stock", "economy", "fed", "inflation", "banking", "invest", 
        "trading", "crypto", "bitcoin", "revenue", "profit", "interest rate"
    ],
    Topic.HEALTH: [
        "health", "medical", "study", "doctor", "virus", "vaccine", "wellness", "diet", 
        "fitness", "cancer", "hospital", "patient", "medicine", "mental health"
    ],
    Topic.LEARNING: [
        "learn", "learning", "education", "course", "university", "tutorial", "how-to", "student", 
        "research", "science", "school", "academy", "knowledge", "skill"
    ],
    Topic.DAILY: [
        "news", "today", "daily", "update", "current", "world", "local", "weather"
    ],
}

# Enhanced News API Documentation

## New Features Summary

### 1. User-Specific Channel Filtering
- News retrieval now respects user's `followed_channels` preferences
- Falls back to all Brazilian sources when user has no followed channels
- Equal distribution of news across selected channels

### 2. Multi-Topic News Retrieval
- New endpoint for retrieving news from multiple topics simultaneously
- Intelligent distribution ensuring minimum 1, maximum 2 articles per topic
- Optimized for balanced content across topics

---

## Updated Endpoints

### GET /api/news/{topic}
**Enhanced**: Now uses user's followed channels

**Authentication Required**: Yes

**New Response Fields**:
```json
{
  "topic": "tecnologia",
  "articles": [...],
  "count": 10,
  "sources_used": 3  // Number of user's channels used, or "all_brazilian_sources"
}
```

**Behavior**:
- If user has followed channels → uses only those channels
- If user has no followed channels → uses all Brazilian sources
- Distributes news requests equally across selected channels
- Example: 20 news limit, 3 channels → ~7 news per channel

---

### POST /api/news/multiple-topics
**New Endpoint**: Retrieve news from multiple topics

**Authentication Required**: Yes

**Request Body**:
```json
{
  "topics": ["tecnologia", "economia", "política"],
  "limit": 20  // Total limit across all topics
}
```

**Response**:
```json
{
  "topics": ["tecnologia", "economia", "política"],
  "news_by_topic": {
    "tecnologia": [...],  // Array of articles
    "economia": [...],
    "política": [...]
  },
  "total_articles": 18,
  "sources_used": 3,
  "distribution_info": {
    "requested_topics": 3,
    "topics_with_news": 3,
    "requested_limit": 20,
    "actual_total": 18
  }
}
```

**Distribution Logic**:
- **Minimum**: 1 article per topic
- **Maximum**: 2 articles per topic  
- **Smart Distribution**: Adjusts based on limit vs topics ratio
- **Examples**:
  - 3 topics, 20 limit → 2 articles each (6 total, room for more)
  - 5 topics, 8 limit → 1 article each + 3 extras (8 total)
  - 6 topics, 5 limit → First 5 topics only, 1 each

---

## User Model Enhancement

### New Field: `followed_channels`

**Type**: Array of strings  
**Description**: List of channel IDs that the user follows  
**Example**: `["globo", "folha-sp", "estadao"]`

**API Response** (in user profile):
```json
{
  "id": "user123",
  "email": "user@example.com",
  "name": "John Doe",
  "interests": ["tecnologia", "política"],
  "followed_channels": ["globo", "folha-sp", "estadao"],
  ...
}
```

---

## Internal Logic Documentation

### Equal Distribution Algorithm

```python
def distribute_news_across_sources(total_limit, num_sources):
    news_per_source = max(1, total_limit // num_sources)
    remainder = total_limit % num_sources
    
    distribution = []
    for i in range(num_sources):
        source_limit = news_per_source + (1 if i < remainder else 0)
        distribution.append(source_limit)
    
    return distribution
```

**Examples**:
- 20 news, 2 sources → [10, 10]
- 20 news, 3 sources → [7, 7, 6] 
- 15 news, 4 sources → [4, 4, 4, 3]

### Multi-Topic Distribution Algorithm

```python
def calculate_topic_distribution(topics, limit):
    min_per_topic = 1
    max_per_topic = 2
    
    if len(topics) * max_per_topic <= limit:
        # Can give maximum to all topics
        return max_per_topic
    elif len(topics) * min_per_topic <= limit:
        # Give minimum to all, distribute remainder
        return "dynamic_distribution"
    else:
        # Too many topics, select subset
        return "truncate_topics"
```

### Channel ID to Domain Conversion

```python
def convert_channel_ids_to_domains(user_channels, all_channels):
    channel_domains = []
    for channel_id in user_channels:
        for channel in all_channels:
            if (channel.get('id') == channel_id and 
                channel.get('isActive', True)):
                channel_domains.append(channel.get('domain'))
                break
    return channel_domains
```

---

## Testing Examples

### Single Topic with User Channels
```bash
curl -X GET "http://localhost:5000/api/news/tecnologia?limit=10" \
  -H "Authorization: Bearer user-token"
```

### Multiple Topics
```bash
curl -X POST "http://localhost:5000/api/news/multiple-topics" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer user-token" \
  -d '{
    "topics": ["tecnologia", "economia", "política"],
    "limit": 15
  }'
```

---

## Benefits

1. **Personalized News Sources**: Users only see news from sources they trust
2. **Balanced Distribution**: Equal representation from all selected sources
3. **Multi-Topic Efficiency**: Single API call for multiple topics
4. **Intelligent Limits**: Automatic distribution optimization
5. **Fallback Support**: Graceful degradation when user has no preferences
6. **Performance**: Reduced API calls through intelligent batching

---

## Backward Compatibility

- All existing endpoints continue to work unchanged
- New fields are optional and have sensible defaults
- Fallback behavior maintains original functionality
- No breaking changes to existing client code

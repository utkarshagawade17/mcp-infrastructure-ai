# MCP Infrastructure Management Console

Natural language interface for Kubernetes and Spectro Cloud Palette infrastructure operations.

## Quick Start

```bash
python mcp_chat.py
```

## Features

- **Natural Language Queries**: Ask questions in plain English
- **Real-time Analysis**: Live infrastructure status and health monitoring
- **Root Cause Diagnosis**: Automated issue detection and analysis
- **Cost Optimization**: Infrastructure spend analysis and recommendations
- **Security Compliance**: Policy validation and compliance checking
- **Multi-Cloud Support**: AWS, Azure, GCP cluster management

## Example Queries

```
Query: Show cluster health status
Query: Why is the payment service failing?
Query: Analyze infrastructure costs
Query: Check security compliance
Query: Recommend configuration for e-commerce workload
```

## Architecture

The system connects to infrastructure APIs (Kubernetes, Palette) and processes
natural language queries to provide operational insights and recommendations.

### Components

- **Query Interface**: Natural language processing for user queries
- **Data Provider**: Infrastructure state retrieval and caching
- **Analysis Engine**: Health scoring, issue detection, cost analysis
- **Recommendation System**: Configuration and optimization suggestions

## Configuration

### API Access

Set API credentials as environment variable:

```bash
export ANTHROPIC_API_KEY="your-api-key"
```

Or configure directly in code (line 179 in mcp_chat.py).

### Data Sources

Currently using mock data for demonstration. For production:

1. Replace `InfrastructureData.get_all_infrastructure_data()` with live API calls
2. Connect to Kubernetes API using kubectl/client libraries
3. Integrate with Palette API endpoints
4. Add authentication and authorization

## Production Deployment

### Requirements

```bash
pip install anthropic
```

### Security Considerations

- Store API keys in secure credential management system
- Implement proper authentication and authorization
- Use read-only API credentials where possible
- Enable audit logging for all queries
- Implement rate limiting

### Scaling

- Add caching layer for frequently accessed data
- Implement query queuing for high-traffic scenarios
- Consider containerization for deployment
- Set up monitoring and alerting

## Development

### Adding New Query Types

Extend the system prompt in `_create_system_prompt()` with new capabilities.

### Custom Data Sources

Implement new methods in `InfrastructureData` class for additional data sources.

### Response Formatting

Modify system prompt to adjust response style and formatting.

## Troubleshooting

### "No API key configured"
- Set ANTHROPIC_API_KEY environment variable
- Or configure API key in code

### "Limited functionality available"
- Running in fallback mode without API access
- Basic queries still supported

### Slow Responses
- Check API connectivity and latency
- Consider caching frequently accessed data

## License

MIT License - See LICENSE file for details

## Support

For issues or questions, contact the development team.

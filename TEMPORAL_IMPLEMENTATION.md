# Temporal.io Implementation for Item Processing

This implementation replaces Celery tasks with Temporal.io workflows for item image processing. Temporal provides better reliability, observability, and fault tolerance compared to traditional task queues.

## Architecture

### Components

1. **Activities** (`temporal_activities.py`): Individual units of work that can fail and be retried
   - `analyze_item_images`: Analyzes uploaded images and generates suggestions
   - `update_item_with_suggestions`: Updates the item with AI-generated suggestions
   - `mark_item_processing_failed`: Marks items as failed when processing errors occur
   - `send_processing_notification`: Sends notifications to users

2. **Workflows** (`temporal_workflows.py`): Orchestrate activities and handle business logic
   - `ItemImageProcessingWorkflow`: Main workflow for processing individual items
   - `ItemBatchProcessingWorkflow`: Workflow for batch processing multiple items

3. **Service Layer** (`temporal_service.py`): High-level interface for starting workflows
   - Provides convenience methods for starting workflows
   - Manages Temporal client connections
   - Handles workflow lifecycle operations

4. **Worker** (`temporal_worker.py`): Executes activities and workflows
   - Registers all activities and workflows
   - Handles connection to Temporal server
   - Provides graceful shutdown

5. **Legacy Compatibility** (`tasks.py`): Maintains Celery-like interface
   - Provides `.delay()` and `.apply_async()` methods
   - Ensures existing code continues to work

## Best Practices Implemented

### Reliability
- **Automatic Retries**: Activities are retried with exponential backoff
- **Error Handling**: Comprehensive error handling with proper logging
- **Timeout Handling**: Activities have appropriate timeouts
- **Workflow Isolation**: Each item gets its own workflow execution

### Observability
- **Structured Logging**: Detailed logging at all levels
- **Workflow History**: Complete audit trail of all operations
- **Status Tracking**: Real-time status updates in the database
- **Monitoring**: Temporal Web UI provides detailed monitoring

### Scalability
- **Horizontal Scaling**: Workers can be scaled independently
- **Parallel Processing**: Batch workflows process items in parallel
- **Resource Management**: Configurable concurrency limits
- **Task Queue Separation**: Different task queues for different workloads

### Development Experience
- **Type Safety**: Full type annotations for better development experience
- **Testing**: Activities are easy to unit test
- **Debugging**: Temporal Web UI provides excellent debugging capabilities
- **Hot Reloading**: Code changes are picked up automatically

## Configuration

### Environment Variables

```bash
# Temporal server configuration
TEMPORAL_ADDRESS=localhost:7233          # Temporal server address
TEMPORAL_NAMESPACE=default               # Temporal namespace
TEMPORAL_TASK_QUEUE=item-processing      # Task queue name

# Worker configuration
TEMPORAL_MAX_CONCURRENT_ACTIVITIES=10    # Max concurrent activities
TEMPORAL_MAX_CONCURRENT_WORKFLOWS=5      # Max concurrent workflows
```

### Docker Compose

The `docker-compose.local.yml` includes:
- Temporal server with PostgreSQL backend
- Temporal Web UI for monitoring
- Temporal worker service
- All necessary dependencies

## Usage

### Starting the System

1. **With Docker Compose**:
   ```bash
   docker-compose -f docker-compose.local.yml up
   ```

2. **Manual Development**:
   ```bash
   # Start Temporal server (if not using Docker)
   temporal server start-dev

   # Start the worker
   python manage.py run_temporal_worker

   # Start Django
   python manage.py runserver
   ```

3. **Using the Startup Script**:
   ```bash
   ./start_with_temporal.sh
   ```

### Triggering Workflows

The existing code continues to work unchanged:

```python
from bubble.items.tasks import process_item_images

# Start processing for an item
workflow_id = process_item_images.delay(item_id)
```

### Monitoring

1. **Temporal Web UI**: http://localhost:8080
2. **Django Admin**: Monitor item processing status
3. **Logs**: Structured logging for all operations

## Migration from Celery

### What Changed
- Task execution now uses Temporal workflows instead of Celery tasks
- Better error handling and retry mechanisms
- Improved observability and monitoring
- More reliable task execution

### What Stayed the Same
- Public API remains unchanged
- Existing code doesn't need modifications
- Same functionality and behavior
- Database models and views unchanged

### Benefits Over Celery
1. **Reliability**: Temporal guarantees task execution
2. **Observability**: Complete workflow history and monitoring
3. **Debugging**: Better debugging tools and visibility
4. **Fault Tolerance**: Automatic recovery from failures
5. **Scalability**: Better horizontal scaling capabilities
6. **Type Safety**: Full type annotations and better IDE support

## Development

### Adding New Activities

```python
@activity.defn
async def my_new_activity(param: str) -> str:
    """New activity implementation."""
    # Your logic here
    return result
```

### Adding New Workflows

```python
@workflow.defn
class MyNewWorkflow:
    @workflow.run
    async def run(self, input_data: str) -> str:
        result = await workflow.execute_activity(
            my_new_activity,
            input_data,
            start_to_close_timeout=timedelta(minutes=5),
        )
        return result
```

### Testing

Activities can be tested as regular async functions:

```python
async def test_analyze_item_images():
    result = await analyze_item_images(item_id=1)
    assert result.title == "Expected Title"
```

## Troubleshooting

### Common Issues

1. **Connection Refused**: Ensure Temporal server is running
2. **Worker Not Starting**: Check worker logs for configuration issues
3. **Workflows Not Executing**: Verify task queue configuration
4. **Database Errors**: Ensure Django can connect to the database

### Debugging

1. Use Temporal Web UI to inspect workflow execution
2. Check worker logs for activity errors
3. Review Django logs for application-level issues
4. Use `temporal workflow show` CLI command for detailed workflow info

### Performance Tuning

1. Adjust worker concurrency settings
2. Optimize activity timeout values
3. Use appropriate retry policies
4. Monitor resource usage and scale accordingly

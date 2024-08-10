import json
from .client import aws_manager, queue_url

def enqueue_json_object(dictionary):
    """
    Enqueue a dictionary as a JSON object to the SQS queue.

    :param dictionary: The dictionary to be enqueued.
    :return: The response from the SQS service.
    """
    # Convert the dictionary to a JSON string
    message_body = json.dumps(dictionary)

    try:
        response = aws_manager.send_sqs_message(
            queue_url=queue_url,
            message_body=message_body,
            message_attributes={
                'ContentType': {
                    'StringValue': 'application/json',
                    'DataType': 'String'
                }
            }
        )
        return response
    except Exception as e:
        print(f"Failed to enqueue JSON object: {str(e)}")
        raise
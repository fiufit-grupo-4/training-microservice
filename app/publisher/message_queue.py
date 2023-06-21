import logging
from fastapi import Request, Response
import datetime


logger = logging.getLogger('app')


def MessageQueueFrom(
    request: Request, response: Response, timestamp: float, response_time: float
):

    date_time = datetime.datetime.fromtimestamp(timestamp)
    formatted_datetime = date_time.strftime(
        "%Y-%m-%d %H:%M:%S.%f"
    )  # datetime obj to ISO 8601 format

    action = ""
    user_id = ""
    training_id = ""
    training_type = ""

    try:
        user_id = request.state.user_id
        action = request.state.action
        training_id = request.state.training_id
        training_type = request.state.training_type

    except Exception as e:
        logger.info(e)
        pass

    return {
        "service": "training-service",
        "path": f'{request.url.path}',
        "url": f'{request.url}',
        "method": f'{request.method}',
        "status_code": f'{response.status_code}',
        "datetime": f'{formatted_datetime}',
        "response_time": f'{response_time}',
        "user_id": f'{user_id}',
        "ip": f'{request.client.host}',
        "country": "",
        "action": f'{action}',
        "training_id": f'{training_id}',
        "training_type": f'{training_type}',
    }

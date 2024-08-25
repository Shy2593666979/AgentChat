from action.send_email.action import send_email_action
from action.google_search.action import google_search_action
from action.arxiv.action import arxiv_action
from action.get_weather.action import get_weather_action
from action.delivery.action import delivery_action

action_class = {
    "EmailAgent": send_email_action,
    "GoogleAgent": google_search_action,
    "ArxivAgent": arxiv_action,
    "WeatherAgent": get_weather_action,
    "DeliveryAgent": delivery_action
}
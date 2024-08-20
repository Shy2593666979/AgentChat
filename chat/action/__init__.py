from action.send_email.action import send_email_action
from action.google_search.action import google_search_action
from action.arxiv.action import arxiv_action

action_class = {
    "send_email": send_email_action,
    "google_search": google_search_action,
    "arxiv": arxiv_action
}
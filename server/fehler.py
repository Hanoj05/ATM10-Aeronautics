"""Gemeinsame Fehlerklasse für den Campus-Dienst."""


class Fehler(Exception):
    """Wird als JSON {"fehler": text} mit HTTP-Status an den Browser gegeben."""

    def __init__(self, status, text):
        super().__init__(text)
        self.status = status
        self.text = text

"""Entry point, so the CRM can be run with: python -m epicevents"""

from epicevents import monitoring
from epicevents.controllers.main import cli

if __name__ == "__main__":
    monitoring.setup()
    cli()
